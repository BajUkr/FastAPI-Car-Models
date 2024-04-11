# FastAPI Car Models API

This project is a RESTful API built with FastAPI for managing car models. It includes endpoints for authentication, CRUD operations on car models, and image upload functionality.

## Features

- JWT-based authentication
- CRUD operations for car models
- Image upload for car models
- Sorting and filtering capabilities for list endpoints

## Installation

To set up the project, you will need Python 3.6+ installed on your machine.

1. **Clone the Repository:**

   ```sh
   git clone https://github.com/BajUkr/FastAPIproject.git
   cd FastAPIproject
   ```

2. **Create a Virtual Environment (Optional but recommended):**

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Requirements:**

   ```sh
   pip install -r requirements.txt
   ```

## Configuration

Before launching the project, ensure you have the correct configuration. Configure the `SECRET_KEY`, `ALGORITHM`, and `ACCESS_TOKEN_EXPIRE_MINUTES` in your environment variables or directly in the code (not recommended for production).

You may also want to create the necessary directories if they are not already set up by the code:

```sh
mkdir uploaded_images
```

## Running the Project

To run the FastAPI server:

```sh
uvicorn main:app --reload
```

The `--reload` flag enables auto-reloading of the server on code changes. This is useful during development but should be omitted in a production environment.

## Authenticated User

Use admin:admin123 to get access to the api endpoints.
Otherwise uncomment add_user_to_database(username, email, password) and type in credentials of your choice.


## API Endpoints

You can access the API documentation and test the endpoints by navigating to `http://127.0.0.1:8000/docs` or `http://127.0.0.1:8000/` in your web browser after starting the server.

Here are the main endpoints provided by the API:

- **POST** `/token`: Authenticate and retrieve an access token.
- **GET** `/users/me/`: Retrieve information about the current user.
- **GET** `/car_models/`: Retrieve a list of car models.
- **POST** `/car_models/`: Create a new car model.
- **GET** `/car_models/{car_model_id}`: Retrieve a specific car model by ID.
- **PUT** `/car_models/{car_model_id}`: Update a specific car model by ID.
- **DELETE** `/car_models/{car_model_id}`: Delete a specific car model by ID.
- **POST** `/car_models/{car_model_id}/image/`: Upload an image for a specific car model.
- **PUT** `/car_models/{car_model_id}/image/`: Update the image for a specific car model.
- **DELETE** `/car_models/{car_model_id}/image/`: Delete the image for a specific car model.
