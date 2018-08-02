## Configuring project on Flask server

*Note:* assuming you have an [Apache](https://www.linux.com/learn/apache-ubuntu-linux-beginners)
working and running.

1. Navigate to `bin` folder in a root of the ci-hpc repository and execute the `start-flask-server.sh`
   ```bash
   bin/start-flask-server.sh
   ```
   And you should see something like this in the terminal window:
   ```bash
   >>> 1.6390 DEBUG: running server
    * Serving Flask app "visualisation.www" (lazy loading)
    * Environment: production
    * Debug mode: off
    * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
   ```

   And if you visit the url `http://0.0.0.0:5000/` in your browser, you shoud see the message:
   ```
   Your server is running!
   ```
2. Edit `index.html` located in `www` folder. Lines 20 and 21 is all you need to change.
   Simple change the values so they match your project and server:
   
   By default project is set to `hello-world` and ip is just a dummy url. The IP you specify must
   be accessible by another computer!
   
   ```js
    projectName: 'hello-world',
    flaskApiUrl: 'http://flask.server.example.com:5000',
   ```

3. Edit visualisation settings for yout project
   The yaml file is located at `cfg/<project>.yaml`. e.g. if you have project with name `foo`, the
   location is `cfg/foo.yaml`
   
   This configuration is reasonably straightforward. You fill out the info about your project and 
   then just say what variables will be used for what cause. Take a look at
   [example](../www/hello-world.yaml) file which explains what variable is for cause.
   
4. Create a symlink to Apache www folder:
   *Note:* assuming you are located at the repository root
   ```
   ln -s $(pwd)/www /var/www/html/ci-hpc
   ```
   
   If you visit http://localhost/ci-hpc you should see the the results.
   
