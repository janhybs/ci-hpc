# Configuring Flask server

*Note:* assuming you have an [Apache](https://www.linux.com/learn/apache-ubuntu-linux-beginners)
working and running.

## Start the flask server with the help of a `bin/server` script:
  ```bash
  bin/server start
  ```
  To test the server is running, execute:
  ```bash
  bin/server status
  ```
  And to stop the running server call:
  ```bash
  bin/server stop
  ```
  And if you visit the url `http://0.0.0.0:5000/` in your browser (it may take couple seconds), you shoud see the message:
  ```
  Your server is running!
  ```
  In opposite case, check the log `ci-hpc.log` located at the repository root or
  try to to execute the script `bin/server` without any arguments (this will
  start the server **not** in the background)

### Configuring the server host and port
  By default the server is accessible for anyone. You can restrict this by scecifying
  `--host=<hostmask>` where `<hostmask>` is the hostname to listen on. Default to `0.0.0.0`.
  
  To change the port of the server API server specify `--port=<portval>` options,
  where `<portval>` is the interger value of your **API** server port.
  
  To see all the options you can change see `bin/server -- --help`.

## Configuring www folder 
  Edit `index.html` located in `www` folder. Lines `41` and `42` is all you need to change.
  Simple change the values so they match your project and server:

  By default project is set to `hello-world` and ip is just a dummy url. The IP you specify must
  be accessible by another computer!

  ```js
  projectName: 'hello-world',
  flaskApiUrl: 'http://flask.server.example.com:5000',
  ```

## Visualisation settings aka what to visualise
  Edit visualisation settings for yout project
  The yaml file is located at `cfg/<project>.yaml`. e.g. if you have project with name `foo`, the
  location is `cfg/foo.yaml`
  
  This configuration is reasonably straightforward. You fill out the info about your project and 
  then just say what variables will be used for what cause. Take a look at
  [example](https://github.com/janhybs/ci-hpc/tree/master/cfg/hello-world) file which explains what variable is for cause.
   
## [optional] Create a symlink to Apache www folder:
  *Note:* assuming you are located at the repository root
  ```
  ln -s $(pwd)/www /var/www/html/ci-hpc
  ```
  
  If you visit http://localhost/ci-hpc you should see the the results.
