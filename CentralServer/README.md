# Project SCARS

Project SCARS is a School Canteen Automated Reporting System for the Department
of Education (DepEd) Schools Division Office (SDO) of the City of Baliwag in
the Philippines.

[![GitHub Last Commit](https://img.shields.io/github/last-commit/Chris1320/ProjectSCARS?path=CentralServer&style=flat&label=Last%20Commit)](https://github.com/Chris1320/ProjectSCARS/tree/main/CentralServer)
[![GitHub Issues or Pull Requests by label](https://img.shields.io/github/issues-raw/Chris1320/ProjectSCARS/scope%20%3E%20central%20server?style=flat&label=Open%20Issues)](https://github.com/Chris1320/ProjectSCARS/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22scope%20%3E%20central%20server%22)
[![Central Server Tests](https://img.shields.io/github/actions/workflow/status/Chris1320/ProjectSCARS/central-server-tests.yml?style=flat&label=Central%20Server%20Tests)](https://github.com/Chris1320/ProjectSCARS/actions/workflows/central-server-tests.yml)
[![Linter Results](https://img.shields.io/github/actions/workflow/status/Chris1320/ProjectSCARS/lint.yml?flat&label=Codebase%20Style)](https://github.com/Chris1320/ProjectSCARS/actions/workflows/lint.yml)
[![Central Server Code Coverage](https://img.shields.io/codecov/c/github/Chris1320/ProjectSCARS?token=BJWS49M1DI&flag=central-server&label=Code%20Coverage&style=flat)](https://app.codecov.io/gh/Chris1320/ProjectSCARS/flags)

<details>
    <summary>Code Coverage Graph</summary>
    <a href="https://codecov.io/gh/Chris1320/ProjectSCARS">
        <img src="https://codecov.io/gh/Chris1320/ProjectSCARS/graphs/sunburst.svg?token=BJWS49M1DI" alt="Code Coverage Graph" />
    </a>
    <p>
        The inner-most circle is the entire project, moving away from the center
        are folders then, finally, a single file. The size and color of each
        slice is representing the number of statements and the coverage,
        respectively.
    </p>
</details>

## Development

[![Central Server Stack](https://skillicons.dev/icons?i=py,fastapi,sqlite,mysql,docker)](#)

The central server is written in Python using the FastAPI framework and
utilizes SQLite or MySQL as its database, depending on the selected
configuration. It also uses either a pure-Python file object storage
or a third-party S3-compatible object storage for storing user avatars
and exported PDFs. It is responsible for handling the backend logic and
storing the submitted data of canteen managers.

### Central Server Requirements

The hard requirements are as follows:

- [Python](https://python.org/) 3.13
- [uv](https://docs.astral.sh/uv/) 0.5.x
- [Docker](https://docker.com/) or [Podman](https://podman.io/)
  - [docker-compose](https://docs.docker.com/compose/) or [podman-compose](https://github.com/containers/podman-compose)

### Central Server Development Setup

1. Install the [required software](#central-server-requirements).
2. Clone the repository.

   ```bash
   git clone https://github.com/Chris1320/ProjectSCARS.git
   ```

3. Navigate to the `CentralServer` directory.

   ```bash
   cd ProjectSCARS/CentralServer
   ```

4. Install dependencies.

   ```bash
   uv sync
   ```

5. Copy and edit the configuration file.

   ```bash
   cp .config.example.json config.json
   uv run ./scripts/secret.py sign     # Generate secure secret keys
   uv run ./scripts/secret.py encrypt  # and write it to `config.json`
   uv run ./scripts/secret.py refresh
   ```

   Edit the `config.json` file to their appropriate values.

6. Select the database you want to use. See [Database Setup](#central-server-database-setup) for more
   information.

7. Select the object store you want to use. See [Object Store Setup](#central-server-object-store-setup)
   for more information.

8. Run the FastAPI development server.

   ```bash
   uv run fastapi dev centralserver --host 0.0.0.0 --port 8081
   ```

> [!IMPORTANT]
> The default credentials are:
>
> - username: `scars`
> - password: `ProjectSCARS1`

#### Central Server Database Setup

The central server supports the following databases:

- SQLite (default)
- MySQL

**Central Server SQLite Database**

To start using SQLite, just edit `./CentralServer/config.json` and adjust the
`database` property to use SQLite. The `connect_args` property is optional
and can be used to pass additional SQLAlchemy connection arguments.

```jsonc
{
  /* ... */
  "database": {
    "type": "sqlite",
    "config": {
      "filepath": "database.db",
      "connect_args": {
        // SQLAlchemy connection arguments
      }
    }
  }
  /* ... */
}
```

On startup, the central server will create a SQLite database file
in the file path specified in the `filepath` property. The default
is `centralserver.db` in the root directory of the central server.

This database is sufficient for development and testing purposes, but
for production use, it is recommended to use MySQL or similar
database server.

**Central Server MySQL Database**

Since SQLite is a file-based database and lacks the ability to run
multiple instances, it is not suitable for production use which needs
high throughput and availability. Therefore, the central server also
supports MySQL as a database. The MySQL database can be run in a
containerized environment using Docker or Podman.

1. Create a `.env` file in `./CentralServer/system/mysql/` using
   the example file.

   ```bash
   cd ./system/mysql/
   cp .env.example .env
   ```

2. Adjust the environment variables in
   `./CentralServer/system/mysql/.env`. For more information
   about MySQL Docker environment variables, see [their documentation](https://hub.docker.com/_/mysql).

3. Run the MySQL container.

   ```bash
   docker-compose up -d # Run this if you are using Docker.
   podman-compose up -d # Run this if you are using Podman.
   cd ../..
   ```

4. If successful, you should be able to access PHPMyAdmin at
   `http://localhost:8083`.

> [!IMPORTANT]
> You might need to log in as the root user in the database
> in the future. The root password is randomly generated,
> which can be seen in the logs of the MySQL container with
> the following format:
>
> `[Note] [Entrypoint]: GENERATED ROOT PASSWORD: bfPy...lqLL`

5. Update `./CentralServer/config.json` to use MySQL. Use the
   same database credentials as the ones in the
   `.env` file. The `connect_args` property is optional and
   can be used to pass additional SQLAlchemy connection
   arguments.

   ```jsonc
   {
     /* ... */
     "database": {
       "type": "mysql",
       "config": {
         "username": "ProjectSCARS_DatabaseAdmin",
         "password": "ProjectSCARS_mysql143",
         "host": "localhost",
         "port": 3306,
         "database": "ProjectSCARS_CentralServer",
         "connect_args": {
           // sqlalchemy connection arguments
         },
       },
     },
     /* ... */
   }
   ```

#### Central Server Object Store Setup

The central server supports the following object stores:

- Local file object store (default)
- MinIO S3-compatible object store

**Local File Object Store**

To start using the local file object store, just edit
`./CentralServer/config.json` and adjust the `object_store` property to match the following structure:

```jsonc
{
  /* ... */
  "object_store": {
    "type": "local",
    "config": {
      "filepath": "./data/",
    },
  },
  /* ... */
}
```

When the central server starts, it will use the provided
filepath to store the files (objects). Make sure that the
filepath is writable by the server. The default is `./data/`
in the root directory of the central server. It is already
created in the repository, so no further action is needed.

Because the local file object store is implemented in the
central server itself, it does not provide any integrity
and redundancy systems. Therefore, it is recommended to
use a dedicated object store for production use, and
use the local file object store only for development
purposes.

**MinIO S3-Compatible Object Store**

Using MinIO, it is possible to provide multiple nodes
to store the objects. This is useful for redundancy and
high availability, therefore it is recommended to be used
in production. The MinIO object store can be run in a
containerized environment using Docker or Podman.

1. Create a `.env` file in `./CentralServer/system/minio/` using
   the example file.

   ```bash
   cd ./system/minio/
   cp .env.example .env
   ```

2. Adjust the environment variables in
   `./CentralServer/system/minio/.env`.

3. Run the MinIO container.

   ```bash
   docker-compose up -d # Run this if you are using Docker.
   podman-compose up -d # Run this if you are using Podman.
   cd ../..
   ```

4. If successful, you should be able to access the MinIO dashboard at
   `http://localhost:8084`.

5. Log in to the dashboard using the credentials in the `.env` file.

6. Navigate to the `Access Keys` tab and create a new access key. Make
   sure to copy the keys, as they will not be shown again.

7. Edit `./CentralServer/config.json` and adjust the `object_store`
   to match the following structure:

   ```jsonc
   {
     /* ... */
     "object_store": {
       "type": "minio",
       "config": {
         "endpoint": "localhost:9000",
         "access_key": "YOUR_ACCESS_KEY",
         "secret_key": "YOUR_SECRET_KEY",
         "secure": false,
       },
     },
     /* ... */
   }
   ```
