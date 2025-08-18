# Implementation Plan

- [x] 1. Update backend Client class to support AWS Bedrock


  - Extend the Client class in client_utils.py to handle bedrock endpoint configuration
  - Add AWS credential parameter mapping (region, access key, secret key)
  - Implement bedrock model name formatting for LiteLLM compatibility
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Add Bedrock model definitions to available models endpoint


  - Update check_available_models function in agent_routes.py to include bedrock provider
  - Define list of available AWS Bedrock Claude models with proper identifiers
  - Ensure bedrock models are returned in the expected format for frontend consumption
  - _Requirements: 1.3, 5.4_

- [x] 3. Update frontend model selection to include Bedrock provider


  - Add "bedrock" to the provider options array in ModelSelectionDialog.tsx
  - Update providerModelOptions state to include bedrock models initialization
  - Ensure bedrock provider appears in the dropdown with other providers
  - _Requirements: 1.1, 1.2_

- [x] 4. Implement AWS credential input fields in the UI


  - Modify the model configuration form to handle AWS-specific fields
  - Map existing UI fields appropriately (API Base for region, API Version for secret key)
  - Add proper field labels and placeholders for AWS credentials
  - Implement field validation for required AWS parameters
  - _Requirements: 1.4, 2.1, 2.2, 2.3_

- [x] 5. Add AWS Bedrock error handling and sanitization


  - Create AWS-specific error message mappings in agent_routes.py
  - Update sanitize_model_error function to handle Bedrock-specific errors
  - Implement user-friendly error messages for common AWS authentication and service errors
  - _Requirements: 3.2, 3.4, 5.2_

- [x] 6. Test Bedrock model connectivity and integration


  - Verify that the test-model endpoint works correctly with Bedrock models
  - Test authentication with both explicit credentials and default credential chain
  - Validate that Bedrock models can be assigned to task slots and used for analysis
  - Test error scenarios and ensure proper error handling
  - _Requirements: 3.1, 3.3, 4.1, 4.2, 4.3, 4.4_

- [x] 7. Update model testing to handle Bedrock-specific scenarios



  - Ensure the test message works correctly with Claude models via Bedrock
  - Implement proper timeout and retry logic for AWS API calls
  - Test rate limiting and throttling scenarios
  - Validate that successful tests enable model assignment to slots
  - _Requirements: 3.1, 3.2, 3.3, 5.3_