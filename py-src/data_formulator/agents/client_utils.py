import litellm
import openai
import boto3
import json
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

class Client(object):
    """
    Returns a LiteLLM client configured for the specified endpoint and model.
    Supports OpenAI, Azure, Ollama, and other providers via LiteLLM.
    """
    def __init__(self, endpoint, model, api_key=None,  api_base=None, api_version=None):
        
        self.endpoint = endpoint
        self.model = model

        # other params, including temperature, max_completion_tokens, api_base, api_version
        self.params = {
            "temperature": 0.7,
        }

        if not (model == "o3-mini" or model == "o1"):
            self.params["max_completion_tokens"] = 1200

        if api_key is not None and api_key != "":
            self.params["api_key"] = api_key
        if api_base is not None and api_base != "":
            self.params["api_base"] = api_base
        if api_version is not None and api_version != "":
            self.params["api_version"] = api_version

        if self.endpoint == "gemini":
            if model.startswith("gemini/"):
                self.model = model
            else:
                self.model = f"gemini/{model}"
        elif self.endpoint == "anthropic":
            if model.startswith("anthropic/"):
                self.model = model
            else:
                self.model = f"anthropic/{model}"
        elif self.endpoint == "azure":
            self.params["api_base"] = api_base
            self.params["api_version"] = api_version if api_version else "2024-02-15-preview"
            if api_key is None or api_key == "":
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
                )
                self.params["azure_ad_token_provider"] = token_provider
            self.params["custom_llm_provider"] = "azure"
        elif self.endpoint == "ollama":
            self.params["api_base"] = api_base if api_base else "http://localhost:11434"
            self.params["max_tokens"] = self.params["max_completion_tokens"]
            if model.startswith("ollama/"):
                self.model = model
            else:
                self.model = f"ollama/{model}"
        elif self.endpoint == "bedrock":
            # Configure for AWS Bedrock - store raw model name without prefix
            self.aws_region = api_base if api_base else "us-east-1"
            self.aws_access_key_id = api_key
            self.aws_secret_access_key = api_version
            # Keep original model name for Bedrock API
            self.model = model
        

    def get_completion(self, messages):
        """
        Returns a completion from the configured model endpoint.
        Supports OpenAI, Azure, Ollama, Bedrock, and other providers.
        """

        if self.endpoint == "openai":
            client = openai.OpenAI(
                base_url=self.params.get("api_base", None),
                api_key=self.params.get("api_key", ""),
                timeout=120
            )

            completion_params = {
                "model": self.model,
                "messages": messages,
            }
            
            if not (self.model == "o3-mini" or self.model == "o1"):
                completion_params["temperature"] = self.params["temperature"]
                completion_params["max_tokens"] = self.params["max_completion_tokens"]
                
            return client.chat.completions.create(**completion_params)
        
        elif self.endpoint == "bedrock":
            return self._get_bedrock_completion(messages)
        
        else:
            return litellm.completion(
                model=self.model,
                messages=messages,
                drop_params=True,
                **self.params
            )

    def _get_bedrock_completion(self, messages):
        """
        Handle AWS Bedrock completion using boto3 directly.
        """
        # Create boto3 client for Bedrock Runtime
        session_kwargs = {
            'region_name': self.aws_region
        }
        
        if self.aws_access_key_id and self.aws_secret_access_key:
            session_kwargs.update({
                'aws_access_key_id': self.aws_access_key_id,
                'aws_secret_access_key': self.aws_secret_access_key
            })
        
        session = boto3.Session(**session_kwargs)
        bedrock_client = session.client('bedrock-runtime')
        
        # Convert messages to Claude format
        system_message = ""
        user_messages = []
        
        for message in messages:
            if message["role"] == "system":
                system_message = message["content"]
            else:
                user_messages.append(message)
        
        # Prepare the request body for Claude
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.params.get("max_completion_tokens", 1200),
            "temperature": self.params.get("temperature", 0.7),
            "messages": user_messages
        }
        
        if system_message:
            body["system"] = system_message
        
        # Make the request to Bedrock
        response = bedrock_client.invoke_model(
            modelId=self.model,
            body=json.dumps(body),
            contentType='application/json'
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # Create a response object that matches the expected format
        class BedrockResponse:
            def __init__(self, content):
                self.choices = [BedrockChoice(content)]
        
        class BedrockChoice:
            def __init__(self, content):
                self.message = BedrockMessage(content)
        
        class BedrockMessage:
            def __init__(self, content):
                self.content = content
                self.role = "assistant"  # Claude always responds as assistant
        
        # Extract content from Claude response
        content = response_body.get('content', [{}])[0].get('text', '')
        
        return BedrockResponse(content)