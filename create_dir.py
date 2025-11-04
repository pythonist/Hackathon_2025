import os

# Base directory
base_dir = "E:/VS code stuff/"

structure = {
  "fraud-app": {
    "app.py": "",
    "fraud_model.json": "",
    "encoder.pkl": "",
    "templates": {
      "index.html": ""
    }
  }
}

# structure =    {
#   "fraud_detection_system": {
#     "backend": {
#       "__init__.py": "",
#       "main.py": "",
#       "config.py": "",
#       "models.py": "",
#       "fraud_predictor.py": "",
#       "nokia_api.py": "",
#       "database.py": ""
#     },
#     "data": {
#       "customer_profiles.json": "",
#       "transactions_log.json": "",
#       "banking_cust_dataset.csv": ""
#     },
#     "models": {
#       "fraud_model.json": "",
#       "encoder.pkl": ""
#     },
#     "scripts": {
#       "prepare_data.py": "",
#       "model_pipeline.py": "",
#       "generate_customer_profiles.py": ""
#     },
#     "frontend": {
#       "index.html": "",
#       "styles.css": "",
#       "app.js": ""
#     },
#     "requirements.txt": "",
#     "run.py": "",
#     "README.md": ""
#   }
# }


# Define folder/file structure as nested dicts
# structure = {
#     "app": {
#         "__init__.py": "",
#         "main.py": "",
#         "routes": {
#             "__init__.py": "",
#             "chat.py": "",
#             "image.py": "",
#             "models.py": ""
#         },
#         "services": {
#             "__init__.py": "",
#             "llm_orchestrator.py": "",
#             "cache.py": "",
#             "rate_limit.py": "",
#             "auth.py": "",
#             "providers": {
#                 "__init__.py": "",
#                 "claude.py": "",
#                 "openai_gpt.py": "",
#                 "gemini.py": "",
#                 "huggingface_text.py": "",
#                 "sd_hf.py": "",
#                 "base.py": ""
#             }
#         },
#         "hybrid": {
#             "__init__.py": "",
#             "ranker.py": "",
#             "merger.py": "",
#             "evaluator_prompt.txt": ""
#         },
#         "utils": {
#             "__init__.py": "",
#             "schemas.py": "",
#             "logging_config.py": "",
#             "errors.py": "",
#             "config.py": ""
#         }
#     },
#     "frontend": {
#         "templates": {
#             "index.html": ""
#         },
#         "static": {
#             "css": {
#                 "app.css": ""
#             },
#             "js": {
#                 "app.js": ""
#             }
#         }
#     },
#     ".env.example": "",
#     "requirements.txt": "",
#     "run.py": "",
#     "README.md": ""
# }

def create_structure(base_path, structure_dict):
    for name, content in structure_dict.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            # Create empty file
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

# Run
create_structure(base_dir, structure)

print(f"Directory structure for '{base_dir}' created successfully!")
