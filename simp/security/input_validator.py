from pydantic import BaseModel, ValidationError, constr
from typing import List, Optional

# Define a Pydantic model for validating intent requests

class IntentRequest(BaseModel):
    intent: constr(min_length=1)  # Intent must be a non-empty string
    entities: Optional[List[constr(strip_whitespace=True)]] = None  # Optional list of entities, trimmed whitespace
    user_id: constr(min_length=1)  # User ID must be a non-empty string

    @classmethod
    def validate_request(cls, data):
        try:
            return cls(**data)
        except ValidationError as e:
            return e.errors()

# Example usage: 
# if __name__ == '__main__':
#     try:
#         request = IntentRequest.validate_request({'intent': 'greet', 'user_id': 'user123'})
#         print(request)
#     except Exception as e:
#         print(e)