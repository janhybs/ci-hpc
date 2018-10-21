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


  $('html > head').append('<style type="text/css" id="cihpc-css"></style>');
  var globalCSS = $('#cihpc-css');
  var cntrlIsPressed: boolean = false;
  var tooltipEnabled: boolean = true;
  $(document).keydown((event: JQuery.Event) => {

    if (event.which == 17) {
      cntrlIsPressed = true;

    } else if (event.which == 16) {
      tooltipEnabled = !tooltipEnabled;
      if (tooltipEnabled) {
        globalCSS.html('');
      } else {
        globalCSS.html('.highcharts-tooltip { display: none !important;}');
      }

    }

  });
  $(document).keyup((event: JQuery.Event) => {
    cntrlIsPressed = false;
  });

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
      CIHPC.init(config);
      CIHPC.addFilters(config);
      CIHPC.addTestList(config);

      $('#modal-options').on('hide.bs.modal', function() {
        Utils.updateOptionGroups();
        CIHPC.showChart(CIHPC.sender);
      });

      $('#benchmark-list a.list-group-item').click(function(e) {
        var $this = $(this);
        $('#benchmark-list a.list-group-item').removeClass('active');
        $this.addClass('active');

        CIHPC.paused = true;
        if ($this.data('mode')) {
          $('#mode-' + $this.data('mode')).click();
        }
        CIHPC.paused = false;
        CIHPC.showChart(this);
      });

      $('#cihpc-option-holder input').change(function(e) {
        Utils.updateOptionGroups();
      });
      
      $('#view-mode').click(function() {
        CIHPC.layout = CIHPC.layout == 'small' ? 'large' : 'small';
        $(this).attr('data-mode', CIHPC.layout);
        $('#charts-sm').attr('data-mode', CIHPC.layout);
        CIHPC.updateAllCharts();
      });

      Utils.updateOptionGroups();
      Utils.createDateSliders();
    }
  });
});
