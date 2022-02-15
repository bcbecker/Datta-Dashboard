# Datta-Dashboard
Datta Dashboard is a single page user dashboard built in React as a proof of concept for using JWT-based token authentication in a microservices architecture. The Flask authentication API on the backend uses in-memory token blacklisting through Redis and a Postgres database to smoothly authenticate users for the dashboard. The deployment is handled by a network of Docker containers, hidden behind a nginx reverse proxy. Security, scaling, and data persistence methods are discussed in depth [here](#design-choices).

There is no live deployment at this time.


## Table of Contents
* [General Info](#general-information)
* [Technologies Used](#technologies-used)
* [Project Structure](#project-structure)
* [Features](#features)
* [Setup](#setup-(using-Docker))
* [Design Choices](#design-choices)
* [Improvements](#improvements)
* [Acknowledgements](#acknowledgements)
* [Datta Able Frontend](#datta-able-react-free-admin-template)


## General Information
Auth Datta Able was built as a means of hitting on key design choices used in modern applications: token-based authentication, client side routing, and a microservices architecture using containerization and a reverse proxy.

In order to accomplish the token-based authentication, JWT (JSON Web Tokens) are used. Using tokens for authentication allows the backend/APIs to be as close to stateless as possible. Instead of keeping track of sessions in a database, we are only keeping track of the blacklisted tokens in Redis for a brief period of time. This means fewer database calls and less overall storage demands.

Client side routing is handled by React, which changes the app's state to manage the components/html rendered in the browser, rather than reloading the page entirely. This style of webapp leads into microservices, which are a way to loosely couple each service, so that they may be easily updated or replaced without taking down the entire application. The containerization and orchestration is taken care of by Docker and docker-compose, respectively. The containerization paired with nginx makes for smooth scaling and deployment, discussed at large [here](#scaling-with-nginx).


## Technologies Used
- React with router, redux, axios, etc.

- Flask, with the Flask-Restx extension
    - Flask-SQLAlchemy as the ORM
    - Flask-Bcrypt for password hashing/checking
    - Flask-JWT-Extended for JWT handling
    - pytest, coverage and fakeredis for testing
    - gunicorn as the production WSGI server

- Redis, with .rdb snapshotting
- PostgreSQL, with the psycopg2 wrapper
- SQLite for development/testing
- nginx as a reverse proxy/server
- Docker for containerization


## Project Structure
~/datta_dashboard
    |-- docker-compose.yml
    |__ /_deployment
        |__ /nginx
            |-- nginx.default.conf
        |__ /postgres
            |-- Dockerfile.postgres
            |__ /db_scripts
                |-- init.sql
        |__ /redis
            |-- Dockerfile.redis
            |-- redis.conf
            |__ /redis-jwt-data
                |-- jwt_dump.rdb
    |__ /client
        |-- Dockerfile.client
        |-- package.json
        |-- yarn.lock
        |__ /public
            |-- ...
        |__ /src
            |-- ...
    |__ /server
        |-- Dockerfile.server
        |-- run.py
        |-- cli.py
        |-- config.py
        |-- requirements.txt
        |-- .env
        |__ /app
            |-- __init__.py
            |-- models.py
            |__ /auth
                |-- __init__.py
                |-- routes.py
                |-- utils.py
        |__ /tests
            |-- __init__.py
            |-- test_auth_routes.py


## Features
- User creation with input validation and sha256 password hashing
- User login granting access to the dashboard
- Implicit token refreshing after requests to prevent unwanted logout
- User logout with token blacklisting in Redis to prevent unauthorized use


## Setup (using Docker)
Ensure you have docker installed.

```bash
docker --version
```

### Creating .env file
For this server to run, you must create a .env file within the package, setting the following parameters:
```bash
cd server
touch .env
```

These are the .env variables, if your host/port/url etc vary, change it accordingly. Note that if you use Docker, your HOSTNAME will be the name of your service as defined in the docker-compose file, not localhost.
```bash
SECRET_KEY=
FLASK_APP=run.py
SQLALCHEMY_DATABASE_URI=sqlite:///<YOUR_DB_NAME>.db
JWT_SECRET_KEY=

DATABASE_URL=postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@<HOSTNAME>:<PORT>/<POSTGRES_DB>
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

REDIS_URL=redis://<HOSTNAME>:<PORT>/<DB>
```
Set the secret key(s) to whatever you'd like (though they should be secure for production). The DATABASE_URL is set aside for a production Postgres db, but the SQLALCHEMY_DATABASE_URI will suffice for testing/local development (SQLite).

### Running the CLI
There is a CLI feature built into the Flask API. The only command added was the flask test command, which takes in a directory to gather and run tests from. In order to do this, we just need to run one command

```bash
cd server
flask test app
```
This will collect and run all the tests from the /app directory and generate a coverage report for each of the files in the directory.
```bash
---------- coverage: platform darwin, python 3.9.0-final-0 -----------
Name                   Stmts   Miss  Cover
------------------------------------------
app/__init__.py           25      1    96%
app/auth/__init__.py       1      0   100%
app/auth/routes.py        72      1    99%
app/auth/utils.py          7      0   100%
app/models.py             26      1    96%
------------------------------------------
TOTAL                    131      3    98%

=================================== 5 passed in 3.98s ====================================
```

### Running the Server
Start the docker daemon and build the containers (sudo if Linux). You may not need to use sudo, or start the daemon, depending on your configuration.

```bash
sudo dockerd
sudo docker-compose up -d --build
```

To ensure everything is up and running, run docker ps
```bash
sudo docker ps
```

Start/stop containers using the following:

```bash
sudo docker container <start/stop> <container-name>
```

Or, stop and remove running containers with:
```bash
sudo docker-compose down
```

### Viewing the website
Site can be found here: http://127.0.0.1:3000/
(for localhost)


## Design Choices

### Frontend
#### Token Handling for API Calls
For handling browser cookie storage on the frontend, I used the js-cookie package. Any time an axios request was made to an endpoint that requires JWT authentication, js-cookie would get the CSRF token from the browser, and send it along in the 'X-CSRF-TOKEN' header, like so:
```js
    ...
        axios.post('/api/users/logout', {}, { headers: { 'X-CSRF-TOKEN': `${Cookies.get('csrf_access_token')}` } })
    ...
```
Note that JavaScript is able to read the 'csrf_access_token' cookie. At first glance, it might seem that this leaves the app susceptible to XSS attacks. However, this is part of the security implementations, which will be discussed more in the backend section. 

For more details on the interworking of the frontend, take a look at the [Datta Able Frontend](#datta-able-react-free-admin-template), created by CodedThemes.

### Backend
#### Token Identity Handling
Upon creation of each user, a uuid is generated and stored as a public_id attribute. The user's public_id is used as the identity (or payload) of the JWT created upon login. Thus, each time that user logs out, their public_id is changed. This is done as an extra precaution to prevent stolen tokens from being decoded and leaking private user data such as emails, usernames, etc.

#### Token Security: CSRF and XSS
When a user logs in, two tokens will be set in their browser: access_token_cookie and csrf_access_token. The prior, access_token_cookie, is set with the httponly tag to prevent JavaScript from being able to read it. In the configuration, there is an option to set the secure tag as well, meaning it will only be sent over a secured channel (over https), which must be used in production. Having the access token be unreadable by JavaScript means that we reduce the likelihood of cross-site scripting (XSS) attacks that would read our cookies, and ultimately, steal our 'identity'!
Protection against cross-site request forgery (CSRF) is where the csrf_access_token cookie comes into play. This cookie is NOT set with the secure tag, meaning it CAN be read by JavaScript. As seen in the [Frontend](#frontend) section, we read the csrf_access_token and pass it along with each request. Even if an attacker is able to read our cookies, the CSRF cookie will not be valid, since it can only be read by the domain that set it (our domain). In this way, we can use the cookie as a double submit token to mitigate CSRF attacks.

#### Token TTL and Redis
Each access token is set with a 15 minute expiration-- or time to live. This means tokens will only be valid for 15 minutes before forcing the user to re-authenticate. Any request to an endpoint with the 'jwt_required' decorator must send a valid access token along with it. The validation is handled in part by the 'token_in_blocklist_loader' utility function. This function can be seen below:
```py
def is_token_in_blocklist(jwt_header: dict, jwt_payload: dict):
    jti = jwt_payload['jti']
    token_in_redis = current_app.redis_blocklist.get(jti)

    return token_in_redis is not None
```
We take a look at the jti (unique identifier) of the token provided with the request, and verify that the token has not been added to the blocklist. Tokens in the blocklist are from users who logged out, and are kept for 15 minutes (the TTL of a token) to ensure they are not reused or used maliciously. Using Redis for the token revocation means that we can run this validation quickly, and implementing a TTL means we can do it without eating up too much memory. 

#### Implicit Token Refreshing
As mentioned, tokens only have 15 minutes to live. However, if a user was to spend 15 minutes viewing their dashboard before trying to make another request, they would be forced to re-authenticate. To avoid this, implicit refreshing after each request is used.
```py
@app.after_request
def refresh_expiring_jwt(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(seconds=(app.TTL.seconds // 2)))

        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            set_access_cookies(response, access_token)

        return response

    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response
```
If a request to an endpoint with the jwt_required decorator is made, and the provided token is over half its TTL old, the token is refreshed. Both a new access token and csrf token are set in the browser cookies automatically. This prevents an active user from being forced to re-authenticate after the token's TTL. Whereas this approach is more simplistic than using a refresh token, there are drawbacks. One such drawback is that after 15 minutes (TTL) of inactivity, the user will be forced to re-authenticate. The implicit refreshing only helps active users to stay active, whereas using a refresh token would allow the user to remain authenticated, regardless of activity, for the life of the refresh token.


### Deployment
#### Dockerfiles
Notice in the project structure that there are several Dockerfiles-- 4 to be exact. Dockerfile.server sets up a container for the Flask API. Dockerfile.redis and Dockerfile.postgres set up redis and postgres containers, each based on the alpine image to keep size down. The postgres Dockerfile has a clever little maneuver:
```
ADD db_scripts/init.sql /docker-entrypoint-initdb.d
RUN chmod a+r /docker-entrypoint-initdb.d/*
```
In the /db_scripts directory, there is a .sql file called init.sql that acts as an entry point for the postgres container, pre-populating the database with the user table and a user entry. This step ensures that the database has some starting data to work with.

The fourth and final Dockerfile is Dockerfile.client. Notice the following commands:
```
FROM node:16-alpine as build-step
...
FROM nginx:stable-alpine
COPY --from=build-step /app/build /usr/share/nginx/html
```
The 'as build-step' syntax allows for a multi-stage build. After we build the React frontend, we only need to keep our /build directory, as that contains all the files needed for deployment. So, in a second build step, we pull the nginx image, and copy the /app/build directory into our nginx server. This way, we can have an nginx container that serves the built React frontend, while remaining as lightweight as possible.

#### Data Persistence
In the docker-compose file, we orchestrate the construction of each of the 4 containers, providing necessary config files and setting up volumes to persist certain data. For example, the redis container has the redis.conf file and /data directories mapped to our own config file and data storage directory.
```
volumes:
    - ./_deployment/redis/redis-jwt-data:/data
    - ./_deployment/redis/redis.conf:/usr/local/etc/redis/redis.conf
```
Within the config, we specified that we want Redis to persist the data in snapshots, stored as .rdb files. RDB is compact, providing fast and easy recovery measures in the instance that the container or Redis server goes down. The current config (line 382 in redis.conf) saves a snapshot every 300 seconds, if at least one record has changed. Of course, this config will need scaled with the application. The tradeoff in using RDB is that the process can be CPU intensive. The BGSAVE command allows for a non-blocking execution of this process, though it is still something to consider with your server's resources.

A similar approach could be taken in the postgres container, persisting any data saved to the db while the container is running. This is exceptionally important in production, where an outage could result in permanent data loss.

#### Scaling with nginx
The microservices architecture used in this project allows for quick scaling, due in part to nginx. The only publicly-exposed port is port 3000 (http), which is our React frontend. This public port is mapped to port 80 (tcp port for http) in the nginx container, where the React content is served. The redis, postgres, and flask containers are all hidden from the public behind the nginx reverse-proxy. This creates a private network that does not need https to communicate securely. In the current configuration, the flask container can communicate with the redis and postgres containers, but they cannot communicate with outside requests. The only requests that come through are via the proxy_pass to the flask API. From the nginx.default.conf:
```
location /api {
        proxy_pass http://api:5000;
    }
```
This passes any requests received by nginx with the /api path to the api container, mapped to port 5000.

So what does this have to do with scaling? Well, if we wanted to add more instances of the flask API in order to reduce load, we simply create an upstream service containing multiple api instances:
```
upstream auth {
    server api1:5000;
    server api2:5000;
    server api3:5000;
}
server {

    ...

    location /api {
        proxy_pass http://auth;
    }
}
```
The upstream service 'auth' is composed of 3 containers, each running the flask-container image. With some slight modifications to the docker-compose file to account for the multiple api containers, the project is ready to deploy. No other changes are necessary to scale the API horizontally, however, we have the option to implement a load balancing algorithm or server weighting as desired. By default, nginx will use round robin with no weighting.

Note: in production, nginx should redirect requests on port 80 to port 443 (https).


## TODO
To Do:
- Expand frontend features (update user, reset password)
- Deploy to AWS using ECS or a Linode server


## Acknowledgements
Thanks to CodedThemes for sharing their Datta Able project!













## Datta Able React Free Admin Template

Datta Able React Free Admin Template made using Bootstrap 4 framework, It is a free lite version of [Datta Able Pro](https://codedthemes.com/item/datta-able-react-free-admin-template/) Dashboard Template that makes you fulfill your Dashboard needs.

![Datta Able React Free Admin Template Preview Image](https://codedthemes.com/wp-content/uploads/edd/2019/05/datta-bootstrap-free.jpg)

Datta Able React Free Admin Template comes with variety of components like Button, Badges, Tabs, Breadcrumb, Icons, Form elements, Table, Charts & Authentication pages.

The code structure is high flexible to use and modify. 

Its design adapts to any screen size easily, even retina screens.

It is modern concept dashboard design with eye catchy colors. Wish you happy to use our product in your project.

### Free Version Preview & Download

Check out live preview of Datta Able lite version & download it.

#### Preview

 - [Demo](http://lite.codedthemes.com/datta-able/react/default/dashboard/default)

#### Download

 - [Download from Github](https://github.com/codedthemes/datta-able-free-react-admin-template)
 - [Download from CodedThemes](https://codedthemes.com/item/datta-able-react-free-admin-template/) & receive important notification instantly in your mail.
 
 ## Premium Version Preview & Download

Datta Able Pro Admin Template is available to purchase. Visit its numerous demos and make your purchase decision.

#### Preview

 - [Demo](https://codedthemes.com/datta-able/react/default/dashboard/default)

#### Download

 - [Purchase from CodedThemes](https://codedthemes.com/item/datta-able-react-admin-template/)

## Table of contents

 * [Getting Started](#getting-started)
 * [Online Documentation](#online-documentation)
 * [Build With](#build-with)
 * [Directory-structure](#directory-structure)
 * [RoadMap](#roadmap)
 * [Author](#author)
 * [Contributing](#contributing)
 * [Issues?](#issues)
 * [License](#license)
 * [Other Dashboard Products](#other-dashboard-products)
 * [Social Profiles](#social-profiles)
 
## Getting Started

Clone from Github 
```
git clone https://github.com/codedthemes/datta-able-bootstrap-dashboard.git
```
*no other dependencies required to run the Datta Able Template*

## Online Documentation

Datta Able Lite version documentation cover in its Pro version documentation - check our [website.](https://codedthemes.com/demos/admin-templates/datta-able/react/docs/)

## Built With

 - [Bootstrap 4](https://getbootstrap.com/)
 - [SASS](https://sass-lang.com/) - SCSS file not included in lite version v1.0
 
## Directory Structure

```
Datta-able/
├── assets/
│   ├── css/
│   │   ├── style.css
│   ├── fonts/
│   │   ├── feather/css/feather.css
│   │   ├── fontawesome/css/fontawesome-all.min.css
│   │   ├── datta/datta-icon.css
│   ├── images/
│   │   ├── user/
│   │   │   ├── avatar-1.jpg
│   │   │   ├── avatar-2.jpg
│   │   │   ├── ...-More
│   │   ├── logo.png
│   │   ├── ...-More
│   ├── js/
│   │   ├── pages/
│   │   │   ├── chart-morris-custom.js
│   │   │   ├── google-maps.js
│   │   ├── vendor-all.min.js
│   │   ├── pcoded.min.js
│   ├── plugins/
│   │   ├── jquery/
│   │   │   ├── js/
│   │   │   │   ├── jquery.min.js
│   │   ├── bootstrap/
│   │   │   ├── css/
│   │   │   │   ├── bootstrap.min.css
│   │   │   ├── js/
│   │   │   │   ├── bootstrap.min.js
│   │   ├── ...-More
├── index.html
├── ...- More
```

## RoadMap

We are continuously working in Datta Able Project and going to make it a awesome dashboard template via your support. Give us the ideas, suggestion for include more components, pages, plugins. Few of future release pages are
 
#### Layouts 
 - Horizontal version
 - Sidebar Image version
 - Introduce Live Customizer (i.e. only for demo)

#### Pages
 - Pricing
 - Login/Register pages version 2
 - User profile
 - Maintenance Pages like 404, Error Pages, Coming Soon 

#### Basic & Advance Components
 - Alert, Cards, Progress, Modal
 - Datepicker, Notification, Slider

*All above pages already included in Pro version. We need your support to include those pages in lite version too.*

## Author

Design and code is completely written by CodedThemes's design and development team. We are happy to welcome the contributors work for our all repositories.

## Issues

Please generate Github issue if you found bug in any version. We are try to be responsive to resolve the issue.

## License

 - Design and Code is Copyright &copy; [CodedThemes](https://www.codedthemes.com)
 - Licensed cover under [MIT](https://github.com/codedthemes/datta-able-bootstrap-dashboard/blob/master/LICENSE)

## Other Dashboard Products

 - [Free Bootstrap 4 Admin Template](https://codedthemes.com/item/category/free-templates/free-bootstrap-admin-templates)
 - [Free React Dashboard Template](https://codedthemes.com/item/category/free-templates/free-react-admin-templates)
 - [Free Angular Dashboard Template](https://codedthemes.com/item/category/free-templates/free-angular-admin-templates)
 - [Premium Bootstrap & Angular Admin Template](https://codedthemes.com/item/category/templates/admin-templates/)
 
## Social Profiles
 - Dribbble [https://dribbble.com/codedthemes](https://dribbble.com/codedthemes)
 - Behance [https://www.behance.net/codedthemes](https://www.behance.net/codedthemes)
 - Facebook [https://www.facebook.com/codedthemes](https://www.facebook.com/codedthemes)
 - Twitter [https://twitter.com/codedthemes](https://twitter.com/codedthemes)
 - Instagram [https://www.instagram.com/codedthemes/](https://www.instagram.com/codedthemes/)