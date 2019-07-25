/// <reference path ="../typings/jquery/jquery.d.ts"/>
/// <reference path ="../typings/nunjucks/nunjucks.d.ts"/>
/// <reference path ="../typings/highcharts/index.d.ts"/>
/// <reference path ="globals.ts"/>
/// <reference path ="filters.ts"/>
/// <reference path ="utils.ts"/>
/// <reference path ="templates.ts"/>
/// <reference path ="cihpc.ts"/>


$(document).ready(() => {
  Globals.initEnv();
  Templates.loadTemplates();
  Utils.extendJQuery();


  CIHPC.url_base = window.cihpc.flaskApiUrl + '/' + window.cihpc.projectName;

  $.ajax({
    url: CIHPC.url_base + '/config',
    error: function (result) {
        $('#configure-view').addClass('disabled');
        $('#charts-sm').html(
          Templates.serverError.render({
            title: 'Server error',
            shortDesc: 'Cannot connect to the server [500]',
            description:  '<p>Could not connect to the server, make sure it is running ' +
                          'and is accesible. The server should be running on this address: ' +
                          '<code>' + CIHPC.url_base + '</code></p>' +
                          '<p>This can be changed in <code>index.html</code> file, in ' +
                          'section:</p><code><pre>' +
                            'window.cihpc = {\n' +
                            '  projectName: "foobar",\n' +
                            '  flaskApiUrl: "http://foo.bar.com:5000",\n' +
                            '}\n' +
                          '</pre></code>'
          })
        );
        // alert(result);
    },
    success: function(config) {
      console.log(config);
      CIHPC.init(config);
      // CIHPC.addFilters(config);
      // CIHPC.addTestList(config);
    }
  });
});
