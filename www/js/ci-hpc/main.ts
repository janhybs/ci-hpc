/// <reference path ="../typings/jquery/jquery.d.ts"/>
/// <reference path ="../typings/nunjucks/nunjucks.d.ts"/>
/// <reference path ="../typings/highcharts/index.d.ts"/>
/// <reference path ="filters.ts"/>
/// <reference path ="utils.ts"/>
/// <reference path ="templates.ts"/>
/// <reference path ="cihpc.ts"/>



interface CIHPCSimple {
  projectName: string;
  flaskApiUrl: string;
}

interface Window {
  cihpc: CIHPCSimple;
  moment: any;
}

interface ExtraData {
  _id: string[];
}

class Globals {
  static env: nunjucks.Environment;

  static initEnv() {
    this.env = nunjucks.configure({});
    this.env.addFilter('toFixed', (num, digits) => {
      return parseFloat(num).toFixed(digits || 2)
    });
    this.env.addFilter('cut', (str, digits) => {
      return str.substring(0, digits || 8)
    });
    this.env.addFilter('max', (values) => {
      return Math.max.apply(Math, values);
    });
    this.env.addFilter('aslist', (value: string) => {
      var s = ''
      value.split('/').forEach((element: string) => {
        if (element) {
          s += '<li>' + element + '</li>';
        }
      })
      return '<ul>' + s + '</ul>';
    });
  }
}


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

  var grabFilter = function(elem: HTMLElement) {
    var $data = $(elem);
    var filters = {};
    var data = (<any>$data).attr();
    for (let key in data) {
      if (key.indexOf('data-filter') == 0) {
        if (key.substring(12)) {
          filters[key.substring(5)] = data[key];
        } else {
          if (data['data-level']) {
            filters[data['data-level']] = data[key];
          }
        }
      }
    }
    return filters;
  }


  var tryToExtractFilters = function(element: HTMLElement) {
    if ($(element).hasClass('list-group-item')) {
      return grabFilter(element);
    }
    return {};
  };

  $.ajax({
    url: CIHPC.url_base + '/config',

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

      Utils.updateOptionGroups();
      Utils.createDateSliders();
    }
  });
});
