<a id="readme-top"></a>

<div align="center">
  <a href="https://github.com/coordnet/transcription-api">
    <img src="logo.png" alt="Logo" width="175" height="175">
  </a>

<h3 align="center">Transcription API</h3>
  <p align="center">
    An API that takes an audio file, queues a job to transcribe the audio using <a href="https://github.com/SYSTRAN/faster-whisper">Faster Whisper</a> returning a job ID, the job ID will return the transcribed text once the job is completed. Files are stored during processing and then deleted unless configured otherwise.
  </p>
</div>

## Development

The simplest way to run the project is using Docker Compose. First, set up the environment:

### Environment

```sh
cp .env.example .env
```

Replace the values in the `.env` file with your own. The `MODEL` value can be one of `tiny.en`, `tiny`, `base.en`, `base`, `small.en`, `small`, `medium.en`, `medium`, `large-v1`, `large-v2`, `large-v3`, `large`, `distil-large-v2`, `distil-medium.en`, `distil-small.en`, `distil-large-v3`.

### Building

Build the images using:

```sh
docker compose build
```

### Running

To run the app for development, use this command:

```sh
docker compose up --watch
```

This will copy the required files to the container from your local machine and will restart the services when necessary.

## Deployment

### Utilizing a GPU

To use Faster Whisper at its full speed, you need to deploy the code to an instance with an Nvidia GPU. The project is already configured to support it.

Edit `.env` and set:

```ini
GPU=1
```

Then build the images with the production compose file:

```sh
docker compose -f compose.yml -f compose.prod.yml build
```

And run it using the same:

```sh
docker compose -f compose.yml -f compose.prod.yml up
```

This should enable the GPU features and run the containers with automatic restarts in case of failure.

### Sentry

To enable Sentry error tracking, edit the `.env` file:

```ini
SENTRY_DSN=__YOUR_DSN__
ENVIRONMENT=production
```

Then restart the Docker Compose command.

## API

Once running, you can access the Swagger documentation at: [http://localhost:3000/apidocs/](http://localhost:3000/apidocs/). Below is an overview of the available endpoints:

### 1. Transcribe an Audio File

#### `POST /transcribe`

**Description:** Upload an audio file for transcription.

**Request Headers:**

- `Content-Type: application/octet-stream`

**Request Body:**

- Raw binary data of the audio file.

**Responses:**

- **201 Created:**
  - Transcription job created successfully.
  - **Example Response:**
    ```jsonc
    {
      "jobId": "string"
    }
    ```
- **400 Bad Request:**
  - No file uploaded or invalid file format.
  - **Example Response:**
    ```jsonc
    {
      "error": "No file uploaded or invalid file format."
    }
    ```
- **500 Internal Server Error:**
  - Server error.
  - **Example Response:**
    ```jsonc
    {
      "error": "Server error."
    }
    ```

---

### 2. Retrieve Job Information

#### `GET /job/{job_id}`

**Description:** Retrieve job information by the job ID.

**Path Parameters:**

- `job_id` (string, required): The unique identifier for the transcription job.

**Responses:**

- **200 OK:**
  - Job information retrieved successfully.
  - **Example Response:**
    ```jsonc
    {
      "jobId": "string",
      "transcription": "Transcribed text here.",
      "filename": "path/to/file.wav",
      "totalDuration": 456.78,
      "runningTime": 123.45,
      "creationDate": "2023-10-05T14:48:00.000Z"
    }
    ```
- **404 Not Found:**
  - Job ID not found.
  - **Example Response:**
    ```jsonc
    {
      "error": "Job ID not found."
    }
    ```
- **500 Internal Server Error:**
  - Server error.
  - **Example Response:**
    ```jsonc
    {
      "error": "Server error."
    }
    ```

---

## Contributing

Please check the [repo issues](https://github.com/coordnet/coordnet/issues) for ideas for contributions and read the [documentation about contributing](CONTRIBUTING.md) for more information.

Any contribution intentionally submitted for inclusion in this repository, shall be dual licensed as below, without any additional terms or conditions.

---

## Acknowledgments

- Some logic for the Whisper transcription was influenced by ideas found in the [WAAS](https://github.com/schibsted/WAAS) project.

---

**Additional Notes:**

- For the `/transcribe` endpoint, ensure that you send the audio file as raw binary data in the body of the request, with the `Content-Type` header set to `application/octet-stream`.
- For the `/transcribe_text` endpoint, send a JSON payload with the `text` field containing the text you wish to process.
- The `/job/{job_id}` endpoint includes `filename` and `totalDuration` fields, which may be `null` if the transcription was created from text input rather than an audio file.
- Error responses are standardized to include an `"error"` field with a descriptive message.

---

## License

Licensed under either of:

- [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0) ([LICENSE-APACHE](LICENSE-APACHE))
- [MIT License](http://opensource.org/licenses/MIT) ([LICENSE-MIT](LICENSE-MIT))

<p align="right">(<a href="#readme-top">back to top</a>)</p>
