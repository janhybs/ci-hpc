var Globals = (function () {
    function Globals() {
    }
    Globals.initEnv = function () {
        this.env = nunjucks.configure({});
        this.env.addFilter('toFixed', function (num, digits) {
            return parseFloat(num).toFixed(digits || 2);
        });
        this.env.addFilter('cut', function (str, digits) {
            return str.substring(0, digits || 8);
        });
        this.env.addFilter('max', function (values) {
            return Math.max.apply(Math, values);
        });
        this.env.addFilter('aslist', function (value) {
            var s = '';
            value.split('/').forEach(function (element) {
                if (element) {
                    s += '<li>' + element + '</li>';
                }
            });
            return '<ul>' + s + '</ul>';
        });
    };
    return Globals;
}());
$(document).ready(function () {
    Globals.initEnv();
    Templates.loadTemplates();
    Utils.extendJQuery();
    $('html > head').append('<style type="text/css" id="cihpc-css"></style>');
    var globalCSS = $('#cihpc-css');
    var cntrlIsPressed = false;
    var tooltipEnabled = true;
    $(document).keydown(function (event) {
        if (event.which == 17) {
            cntrlIsPressed = true;
        }
        else if (event.which == 16) {
            tooltipEnabled = !tooltipEnabled;
            if (tooltipEnabled) {
                globalCSS.html('');
            }
            else {
                globalCSS.html('.highcharts-tooltip { display: none !important;}');
            }
        }
    });
    $(document).keyup(function (event) {
        cntrlIsPressed = false;
    });
    CIHPC.url_base = window.cihpc.flaskApiUrl + '/' + window.cihpc.projectName;
    var grabFilter = function (elem) {
        var $data = $(elem);
        var filters = {};
        var data = $data.attr();
        for (var key in data) {
            if (key.indexOf('data-filter') == 0) {
                if (key.substring(12)) {
                    filters[key.substring(5)] = data[key];
                }
                else {
                    if (data['data-level']) {
                        filters[data['data-level']] = data[key];
                    }
                }
            }
        }
        return filters;
    };
    var tryToExtractFilters = function (element) {
        if ($(element).hasClass('list-group-item')) {
            return grabFilter(element);
        }
        return {};
    };
    $.ajax({
        url: CIHPC.url_base + '/config',
        success: function (config) {
            CIHPC.init(config);
            CIHPC.addFilters(config);
            CIHPC.addTestList(config);
            $('#modal-options').on('hide.bs.modal', function () {
                Utils.updateOptionGroups();
                CIHPC.showChart(CIHPC.sender);
            });
            $('#benchmark-list a.list-group-item').click(function (e) {
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
            $('#cihpc-option-holder input').change(function (e) {
                Utils.updateOptionGroups();
            });
            Utils.updateOptionGroups();
            Utils.createDateSliders();
        }
    });
});
