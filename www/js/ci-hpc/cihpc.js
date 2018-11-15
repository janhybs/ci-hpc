var CIHPC = (function () {
    function CIHPC() {
    }
    CIHPC._getCommitUrl = function (git_url) {
        var tmp = git_url.replace('http://', '').replace('https://', '');
        if (!!~tmp.indexOf('bitbucket.org')) {
            return git_url + '/commits';
        }
        return git_url + '/commit';
    };
    CIHPC.addTestList = function (config) {
        $('#benchmark-list').empty();
        $('#benchmark-list').html(Templates.benchmarkList.render({
            title: config.name,
            desc: config.desc,
            git_url: config['git-url'],
            tests: config.tests
        }));
    };
    ;
    CIHPC.addFilters = function (config) {
        var testView = config['test-view'];
        var fields = config['fields'];
        $('#cihpc-option-holder').empty();
        $('#cihpc-option-holder').append(Templates.dateSliders.render({
            text: 'Commit range',
            key: 'range',
            items: [
                { name: 'from', value: 'min', title: 'From' },
                { name: 'to', value: 'max', title: 'To' },
            ]
        }));
        $('#cihpc-option-holder').append(Templates.dateSliders.render(ConfigureViewFilters.filterCommitSqueeze));
        $('#cihpc-option-holder').append('<hr />');
        if (fields['problem.cpu']) {
            $('#cihpc-option-holder').append(Templates.groupToggle.render(ConfigureViewFilters.filterMode));
        }
        $('#cihpc-option-holder').append('<hr />');
        if (testView.groupby) {
            var groupby = [];
            for (var key in testView.groupby) {
                groupby.push({
                    text: testView.groupby[key],
                    name: key,
                    checked: true,
                    desc: '[user option] if checked, will split the results into groups' +
                        'based on <code>' + key + '</code> value each group will have its own chart.'
                });
            }
            $('#cihpc-option-holder').append(Templates.groupToggle.render({
                text: 'Group by',
                key: 'groupby',
                items: groupby.concat(ConfigureViewFilters.filterGroupBy(fields))
            }));
        }
        $('#cihpc-option-holder').append('<hr />');
        $('#cihpc-option-holder').append(Templates.groupToggle.render(ConfigureViewFilters.filterSeries));
    };
    ;
    CIHPC.init = function (config) {
        CIHPC.git_url = config['git-url'];
        CIHPC.commit_url = CIHPC._getCommitUrl(CIHPC.git_url);
        CIHPC.testDict = {};
        document.title = config.name;
        if (config.logo) {
            $('#logo').attr('src', config.logo);
        }
        var testLevelName = config.fields['problem.test'], caseLevelName = config.fields['problem.case'], subCaseLevelName = config.fields['problem.subcase'];
        for (var testLevel in config.tests) {
            var testItem = config.tests[testLevel];
            CIHPC.testDict['test-' + testItem.name] = $.extend({}, CIHPC.getFilters(testItem, testItem.level === undefined ? testLevelName : testItem.level));
            for (var caseLevel in testItem.tests) {
                var caseItem = testItem.tests[caseLevel];
                CIHPC.testDict['test-' + testItem.name + '-' + caseItem.name] = $.extend(CIHPC.getFilters(caseItem, caseItem.level === undefined ? caseLevelName : caseItem.level), CIHPC.getFilters(testItem, testItem.level === undefined ? testLevelName : testItem.level));
                for (var subcaseLevel in caseItem.tests) {
                    var subcaseItem = caseItem.tests[subcaseLevel];
                    CIHPC.testDict['test-' + testItem.name + '-' + caseItem.name + '-' + subcaseItem.name] = $.extend(CIHPC.getFilters(subcaseItem, subcaseItem.level === undefined ? subCaseLevelName : subcaseItem.level), CIHPC.getFilters(caseItem, caseItem.level === undefined ? caseLevelName : caseItem.level), CIHPC.getFilters(testItem, testItem.level === undefined ? testLevelName : testItem.level));
                }
            }
        }
    };
    ;
    CIHPC.showFrameViewChart = function (chartID, selectedIDs) {
        var options = $.extend(Utils.grabOptions(), {
            filters: CIHPC.grabFilters(CIHPC.sender),
            _ids: selectedIDs
        });
        var strOptions = btoa(JSON.stringify(options));
        $.ajax({
            url: CIHPC.url_base + '/frame-view/' + strOptions,
            error: function (error) {
                console.log({ error: error });
                alert(error);
            },
            success: function (result) {
                console.log({ result: result });
                $('.bd-sidebar').animate({ scrollTop: 0 }, 300);
                var opts = result.data[0];
                opts.tooltip = {
                    formatter: function () {
                        console.log(this);
                        if (this.hasOwnProperty('points')) {
                            return Templates.barTooltip.render(this);
                        }
                        else {
                            return Templates.barTooltip.render({
                                points: [this],
                                x: this.x,
                                y: this.y
                            });
                        }
                    }
                };
                $('#frame-detail-' + chartID).highcharts('SparkBar', opts);
                $('#col-' + chartID).addClass('has-detail');
                $('#col-' + chartID).trigger('updateFullscreen', [true]);
            }
        });
    };
    ;
    CIHPC.paused = false;
    CIHPC.layout = 'medium';
    CIHPC.layouts = ['medium', 'large', 'small'];
    CIHPC.getFilters = function (opts, level) {
        var result = $.extend({}, opts.filters);
        if (level === null) {
            return result;
        }
        result[level] = opts.name;
        return result;
    };
    CIHPC.grabFilters = function (elem) {
        return CIHPC.testDict[elem.id];
    };
    CIHPC.showHistory = function () {
        $('#loader').show();
        $('#charts-sm').empty();
        $.ajax({
            url: CIHPC.url_base + '/commit-history',
            error: function (error) {
                console.log({ error: error });
                $('#loader').hide();
                alert('fatal error');
            },
            success: function (result) {
                console.log(result[0]);
                $('#loader').hide();
                $('#charts-sm').html(Templates.commitHistory.render({
                    id: 'commit-history-table',
                    commit_url: CIHPC.commit_url,
                    keys: Object.keys(result[0]),
                    items: result
                }));
                $('#commit-history-table').DataTable({
                    searching: false,
                    paging: false,
                    autoWidth: false
                });
            }
        });
    };
    CIHPC.destroyAllCharts = function () {
        if (Highcharts.charts) {
            for (var _i = 0, _a = Highcharts.charts; _i < _a.length; _i++) {
                var chart = _a[_i];
                if (chart) {
                    chart.destroy();
                }
            }
        }
    };
    CIHPC.updateAllCharts = function () {
        if (Highcharts.charts) {
            for (var _i = 0, _a = Highcharts.charts; _i < _a.length; _i++) {
                var chart = _a[_i];
                if (chart) {
                    chart.setSize(null, null, false);
                }
            }
        }
    };
    CIHPC.showChart = function (sender) {
        if (CIHPC.paused) {
            return;
        }
        if (!sender) {
            return;
        }
        CIHPC.destroyAllCharts();
        CIHPC.sender = sender;
        var options = $.extend(Utils.grabOptions(), {
            filters: CIHPC.grabFilters(sender)
        });
        var strOptions = btoa(JSON.stringify(options));
        $('#loader').show();
        $('#charts-sm').empty();
        $.ajax({
            url: CIHPC.url_base + '/sparkline-view/' + strOptions,
            error: function (error) {
                console.log({ error: error });
                $('#loader').hide();
                alert('fatal error');
            },
            success: function (result) {
                console.log({ result: result });
                $('#loader').hide();
                if (result.status != 200) {
                    $('#charts-sm').html(Templates.emptyResults.render(result));
                    return;
                }
                $('#charts-sm').empty();
                for (var i in result.data) {
                    var chart = result.data[i];
                    var extra = chart.extra;
                    var id = 'chart-' + (Number(i) + 1);
                    $('#charts-sm').append(Templates.cardChartSm.render({ id: id, title: chart.title, extra: extra }));
                    chart.xAxis.labels = {
                        formatter: function () {
                            var commits = this.axis.series[this.axis.series.length - 1].userOptions.extra.commits[this.pos][0];
                            if (commits.length == 1) {
                                var link = CIHPC.commit_url + '/' + commits[0];
                                return '<a class="xaxis-link pt-4" href="' + link + '" target="_blank">' + this.value + '</a>';
                            }
                            else {
                                var links = [];
                                var atonce = [];
                                for (var _i = 0, commits_1 = commits; _i < commits_1.length; _i++) {
                                    var commit = commits_1[_i];
                                    var link = CIHPC.commit_url + '/' + commit;
                                    links.push('<a class="xaxis-link" href="' + link + '" target="_blank">' + commit.substr(0, 6) + '</a>');
                                    atonce.push("window.open('" + link + "')");
                                }
                                return this.value + ' <a href="#" onclick="' + atonce.join('; ') + '">open all</a> <br /> (' +
                                    (links.join(', ')) + ')';
                            }
                        }
                    };
                    $('#' + id).highcharts('SparkMedium', chart);
                    $('#' + id).on('point-select', function (target, point) {
                        var chartID = this.id;
                        var points = point.series.chart.getSelectedPoints();
                        points.push(point);
                        var selectedIDs = [];
                        for (var _i = 0, points_1 = points; _i < points_1.length; _i++) {
                            var point_1 = points_1[_i];
                            var extra = point_1.series.userOptions.extra;
                            selectedIDs = selectedIDs.concat(extra._id[point_1.index]);
                        }
                        CIHPC.showFrameViewChart(chartID, selectedIDs);
                    });
                }
                $('.spark-holder').on('updateFullscreen', function (event, value) {
                    var $col = $(this);
                    var chart = $col.find('.chart-holder.main').highcharts();
                    var detail = $col.find('.chart-holder.detail').highcharts();
                    console.log($col.find('.chart-holder.main').width());
                    if (value) {
                        $col.addClass('expanded fullscreen p-1');
                    }
                    else {
                        $col.removeClass('expanded fullscreen p-1');
                    }
                    console.log($col.find('.chart-holder.main').width());
                    chart.reflow();
                    if (detail) {
                        detail.reflow();
                    }
                    console.log($col.find('.chart-holder.main').width());
                    chart.reflow();
                    if (detail) {
                        detail.reflow();
                    }
                });
                $('.sparkline-fullscreen').click(function (e) {
                    var $col = $($(this).data('target'));
                    $col.trigger('updateFullscreen', [!$col.hasClass('expanded')]);
                });
                if (result.data.length == 1) {
                    $('.sparkline-fullscreen').click();
                }
            }
        });
    };
    return CIHPC;
}());
