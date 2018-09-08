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
    };
    return Globals;
}());
var Templates = (function () {
    function Templates() {
    }
    Templates.loadTemplates = function () {
        var compileNow = true;
        this.cardChartSm = Globals.env.getTemplate("templates/mdb/card-chart-sm.njk", compileNow);
        this.benchmarkList = Globals.env.getTemplate("templates/mdb/benchmark-list.njk", compileNow);
        this.groupToggle = Globals.env.getTemplate("templates/mdb/group-toggle.njk", compileNow);
    };
    return Templates;
}());
$(document).ready(function () {
    Globals.initEnv();
    Templates.loadTemplates();
    window.lastQuery = {};
    (function (old) {
        $.fn.attr = function () {
            if (arguments.length === 0) {
                if (this.length === 0) {
                    return null;
                }
                var obj = {};
                $.each(this[0].attributes, function () {
                    if (this.specified) {
                        obj[this.name] = this.value;
                    }
                });
                return obj;
            }
            return old.apply(this, arguments);
        };
    })($.fn.attr);
    var cntrlIsPressed = false;
    $(document).keydown(function (event) {
        if (event.which == 17)
            cntrlIsPressed = true;
    });
    $(document).keyup(function (event) {
        cntrlIsPressed = false;
    });
    window.cihpc = {
        projectName: 'flow123d',
        flaskApiUrl: 'http://hybs.nti.tul.cz:5000'
    };
    var url_base = window.cihpc.flaskApiUrl + '/' + window.cihpc.projectName;
    var commit_url = null;
    var testDict = {};
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
    var obj2str = function (o, separator, glue) {
        if (separator === void 0) { separator = ","; }
        if (glue === void 0) { glue = "="; }
        return $.map(Object.getOwnPropertyNames(o), function (k) { return [k, o[k]].join(glue); }).join(separator);
    };
    var obj2arr = function (o, glue) {
        if (glue === void 0) { glue = "="; }
        return $.map(Object.getOwnPropertyNames(o), function (k) { return [k, o[k]].join(glue); });
    };
    var createArgParams = function (obj, prefix) {
        if (prefix === void 0) { prefix = 'ff='; }
        return obj2arr(obj).map(function (v) { return prefix + v; });
    };
    var grabOptions = function () {
        var opts = {};
        console.log(opts);
        $('#cihpc-option-holder .btn input[type="checkbox"]').each(function (index, item) {
            console.log(item);
            var isChecked = $(this).is(':checked');
            var optGroup = $(this).data('key');
            if (optGroup) {
                if (!opts[optGroup]) {
                    opts[optGroup] = {};
                }
                opts[optGroup][$(this).attr('name')] = isChecked;
            }
            else {
                opts[$(this).attr('name')] = isChecked;
            }
        });
        console.log(opts);
        $('#cihpc-option-holder .btn input[type="radio"]:checked').each(function (index, item) {
            console.log(item);
            var optGroup = $(this).data('key');
            if (optGroup) {
                if (!opts[optGroup]) {
                    opts[optGroup] = {};
                }
                opts[optGroup][$(this).attr('name')] = $(this).val();
            }
            else {
                opts[$(this).attr('name')] = $(this).val();
            }
        });
        console.log(opts);
        return opts;
    };
    var grabFilters = function (elem) {
        return testDict[elem.id];
    };
    var tryToExtractFilters = function (element) {
        if ($(element).hasClass('list-group-item')) {
            return grabFilter(element);
        }
        return {};
    };
    $.ajax({
        url: url_base + '/config',
        success: function (config) {
            document.title = config.name;
            var commit_url = config['git-url'] +
                (!!config['git-url'].indexOf('https://bitbucket.org') ? '/commit/' : '/commits/');
            if (config.logo) {
                $('#logo').attr('src', config.logo);
            }
            var testView = config['test-view'];
            if (testView.groupby) {
                var groupby = [];
                for (var key in testView.groupby) {
                    groupby.push({ text: key, name: testView.groupby[key], checked: true });
                }
                $('#cihpc-option-holder').empty();
                $('#cihpc-option-holder').append(Templates.groupToggle.render({
                    name: 'grouping',
                    key: 'groups',
                    items: groupby
                }));
            }
            if (testView['cpu-property']) {
                $('#cihpc-option-holder').append(Templates.groupToggle.render({
                    name: 'scaling',
                    desc: 'Choose the display mode',
                    radio: true,
                    items: [
                        { text: 'none', name: 'none', checked: true },
                        { text: 'strong', name: 'strong', checked: false },
                        { text: 'weak', name: 'weak', checked: false },
                    ]
                }));
            }
            $('#cihpc-option-holder').append(Templates.groupToggle.render({
                name: 'options',
                desc: 'Turn off additional series to save space and computing time',
                items: [
                    { text: 'show boxplot', name: 'show-boxplot', checked: false },
                    { text: 'show errorbar', name: 'show-errorbar', checked: true },
                ]
            }));
            $('#benchmark-list').empty();
            $('#benchmark-list').html(Templates.benchmarkList.render({
                title: config.name,
                tests: config.tests
            }));
            var getFilters = function (opts, level) {
                var result = $.extend({}, opts.filters);
                if (level === null) {
                    return result;
                }
                result[level] = opts.name;
                return result;
            };
            for (var testLevel in config.tests) {
                var testItem = config.tests[testLevel];
                testDict['test-' + testItem.name] = $.extend({}, getFilters(testItem, testItem.level === undefined ? '.test' : testItem.level));
                for (var caseLevel in testItem.tests) {
                    var caseItem = testItem.tests[caseLevel];
                    testDict['test-' + testItem.name + '-' + caseItem.name] = $.extend(getFilters(caseItem, caseItem.level === undefined ? '.case' : caseItem.level), getFilters(testItem, testItem.level === undefined ? '.test' : testItem.level));
                    for (var scaleLevel in caseItem.tests) {
                        var scaleItem = caseItem.tests[scaleLevel];
                        testDict['test-' + testItem.name + '-' + caseItem.name + '-' + scaleItem.name] = $.extend(getFilters(scaleItem, scaleItem.level === undefined ? '.scale' : scaleItem.level), getFilters(caseItem, caseItem.level === undefined ? '.case' : caseItem.level), getFilters(testItem, testItem.level === undefined ? '.test' : testItem.level));
                    }
                }
            }
            $('#benchmark-list a.list-group-item').click(function (e) {
                var $this = $(this);
                window.cihpc.paused = true;
                if ($this.data('mode')) {
                    $('#' + $this.data('mode')).click();
                }
                window.cihpc.paused = false;
                showChart(this);
            });
            $('#cihpc-option-holder .btn input').change(function (e) {
                showChart(window.lastQuery.sender);
            });
            $('[data-toggle="tooltip"]').tooltip();
            var showChart = function (sender) {
                if (window.cihpc.paused) {
                    return;
                }
                if (!sender) {
                    return;
                }
                var options = grabOptions();
                var filters = grabFilters(sender);
                window.lastQuery.sender = sender;
                options['filters'] = filters;
                var strOptions = btoa(JSON.stringify(options));
                console.log(options);
                $.ajax({
                    url: url_base + '/sparkline-view/' + strOptions,
                    error: function (result) {
                        alert(result);
                    },
                    success: function (opts) {
                        $('#charts-sm').empty();
                        for (var i in opts.data) {
                            var size = opts.data[i].size;
                            var opt = opts.data[i].data;
                            var id = 'chart-' + (Number(i) + 1);
                            $('#charts-sm').append(Templates.cardChartSm.render({ id: id, title: opt.title.text }));
                            opt.title.text = null;
                            opt.xAxis.labels = {
                                useHTML: true,
                                formatter: function () {
                                    var commit = this.axis.series[0].options.commits[this.pos];
                                    var link = commit_url + commit;
                                    return '<a href="' + link + '" target="_blank">' + this.value + '</a>';
                                }
                            };
                            $('#' + id).highcharts('SparkMedium', opt);
                        }
                        $('.sparkline-fullscreen').click(function (e) {
                            var cls = 'col-xl-6';
                            var $col = $($(this).data('target'));
                            var chart = $col.find('.chart-holder').highcharts();
                            if ($col.hasClass(cls)) {
                                $col.removeClass(cls);
                                chart.setSize(null, 640, false);
                            }
                            else {
                                $col.addClass(cls);
                                chart.setSize(null, 340, false);
                            }
                        });
                        if (opts.data.length == 1) {
                            $('.sparkline-fullscreen').click();
                        }
                    }
                });
            };
        }
    });
});
