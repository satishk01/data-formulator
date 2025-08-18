# Design Document

## Overview

This design document outlines the implementation approach for adding AWS Bedrock Anthropic Claude model support to the Data Formulator application. The solution will integrate AWS Bedrock through LiteLLM's existing Bedrock support, extending the current Client class and updating the frontend model selection interface.

The design leverages LiteLLM's built-in AWS Bedrock integration, which handles the AWS SDK authentication and API communication, while maintaining consistency with the existing provider architecture.

## Architecture

### High-Level Architecture

The AWS Bedrock integration follows the existing provider pattern:

```
Frontend (ModelSelectionDialog) 
    ↓ (user selects bedrock provider)
Backend (agent_routes.py)
    ↓ (creates Client with bedrock endpoint)
Client (client_utils.py)
    ↓ (configures LiteLLM for bedrock)
LiteLLM
    ↓ (handles AWS SDK communication)
AWS Bedrock API
```

### Integration Points

1. **Frontend Model Selection**: Add "bedrock" to the provider options list
2. **Client Configuration**: Extend Client class to handle bedrock-specific parameters
3. **Model Discovery**: Update available models endpoint to include Bedrock Claude models
4. **Authentication**: Support AWS credential configuration through the UI

## Components and Interfaces

### Frontend Components

#### ModelSelectionDialog.tsx Updates
- Add "bedrock" to the provider options array: `['openai', 'azure', 'ollama', 'anthropic', 'gemini', 'bedrock']`
- Update providerModelOptions state to include bedrock models
- Add conditional UI fields for AWS-specific configuration:
  - AWS Region (required)
  - AWS Access Key ID (optional - can use default credential chain)
  - AWS Secret Access Key (optional - can use default credential chain)
  - AWS Session Token (optional - for temporary credentials)

#### UI Field Mapping
- **Provider**: "bedrock"
- **API Key**: AWS Access Key ID (reuse existing field)
- **API Base**: AWS Region (repurpose existing field with different label)
- **API Version**: AWS Secret Access Key (repurpose existing field with different label)
- **Additional Field**: AWS Session Token (may need new field or use existing pattern)

### Backend Components

#### client_utils.py Updates

Add bedrock endpoint handling in the Client class `__init__` method:

```python
elif self.endpoint == "bedrock":
    # Configure for AWS Bedrock
    if api_base:  # Region
        self.params["aws_region_name"] = api_base
    if api_key:  # AWS Access Key ID
        self.params["aws_access_key_id"] = api_key
    if api_version:  # AWS Secret Access Key
        self.params["aws_secret_access_key"] = api_version
    
    # Format model name for LiteLLM bedrock format
    if not model.startswith("bedrock/"):
        self.model = f"bedrock/{model}"
    else:
        self.model = model
```

#### agent_routes.py Updates

Update the `check_available_models()` function to include bedrock models:

```python
providers = ['openai', 'azure', 'anthropic', 'gemini', 'ollama', 'bedrock']

# Add bedrock model definitions
bedrock_models = [
    'anthropic.claude-3-5-sonnet-20241022-v2:0',
    'anthropic.claude-3-5-sonnet-20240620-v1:0', 
    'anthropic.claude-3-5-haiku-20241022-v1:0',
    'anthropic.claude-3-opus-20240229-v1:0',
    'anthropic.claude-3-sonnet-20240229-v1:0',
    'anthropic.claude-3-haiku-20240307-v1:0'
]
```

## Data Models

### Model Configuration Schema

The existing ModelConfig interface will be extended to support AWS Bedrock:

```typescript
interface ModelConfig {
    id: string;
    endpoint: string;  // "bedrock"
    model: string;     // e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0"
    api_key?: string;  // AWS Access Key ID
    api_base?: string; // AWS Region (e.g., "us-east-1")
    api_version?: string; // AWS Secret Access Key
    // Additional field for session token if needed
}
```

### AWS Credential Handling

The system will support multiple authentication methods:

1. **Explicit Credentials**: Access Key ID + Secret Access Key provided via UI
2. **Default Credential Chain**: When no credentials provided, rely on:
   - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
   - IAM roles (for EC2/ECS deployments)
   - AWS credential files (~/.aws/credentials)

## Error Handling

### AWS-Specific Error Scenarios

1. **Authentication Errors**
   - Invalid credentials
   - Expired session tokens
   - Insufficient permissions

2. **Service Errors**
   - Model not available in region
   - Rate limiting/throttling
   - Service quotas exceeded

3. **Configuration Errors**
   - Invalid region specification
   - Malformed model identifiers

### Error Message Mapping

The system will provide user-friendly error messages for common AWS Bedrock errors:

```python
def sanitize_bedrock_error(error_message):
    aws_error_mappings = {
        'UnauthorizedOperation': 'Invalid AWS credentials or insufficient permissions',
        'ThrottlingException': 'Request rate limit exceeded. Please try again later',
        'ModelNotAvailableException': 'Selected model is not available in the specified region',
        'ValidationException': 'Invalid request parameters. Please check your configuration'
    }
    # Apply mappings and return sanitized message
```

## Testing Strategy

### Unit Tests

1. **Client Configuration Tests**
   - Test bedrock endpoint initialization
   - Verify parameter mapping (region, credentials)
   - Test model name formatting

2. **Authentication Tests**
   - Test explicit credential configuration
   - Test default credential chain fallback
   - Test session token handling

### Integration Tests

1. **Model Testing Endpoint**
   - Test successful model communication
   - Test authentication failure scenarios
   - Test region/model availability validation

2. **End-to-End Tests**
   - Test complete workflow from UI to model response
   - Test error handling and user feedback
   - Test model assignment to task slots

### Manual Testing Scenarios

1. **Configuration Testing**
   - Test UI field validation
   - Test credential input and storage
   - Test model selection and testing

2. **Functional Testing**
   - Test data analysis tasks with Bedrock models
   - Test error recovery and fallback behavior
   - Test performance and response times

## Implementation Considerations

### Security

- AWS credentials will be handled securely, following the same patterns as other API keys
- Credentials will not be logged or exposed in error messages
- Support for IAM roles and temporary credentials for enhanced security

### Performance

- LiteLLM handles connection pooling and request optimization
- AWS Bedrock regional deployment considerations for latency
- Proper timeout and retry configuration

### Scalability

- Support for multiple AWS regions
- Future extensibility for other AWS Bedrock models (non-Anthropic)
- Configuration management for enterprise deployments

### Dependencies

- LiteLLM already includes AWS Bedrock support
- No additional Python dependencies required
- Frontend changes are minimal and follow existing patterns