class Templates {
    static testList: nunjucks.Template;
    static lineTooltip: nunjucks.Template;
    static chart: nunjucks.Template;
    static emptyResults: nunjucks.Template;
    static toggleOptions: nunjucks.Template;

    static cardChartSm: nunjucks.Template;
    static benchmarkList: nunjucks.Template;
    static groupToggle: nunjucks.Template;
    static barTooltip: nunjucks.Template;
    static dateSliders: nunjucks.Template;

    static serverError: nunjucks.Template;
    static commitHistory: nunjucks.Template;

    static loadTemplates() {
        var compileNow: boolean = true;

        this.cardChartSm = Globals.env.getTemplate("templates/mdb/card-chart-sm.njk", compileNow);
        this.benchmarkList = Globals.env.getTemplate("templates/mdb/benchmark-list.njk", compileNow);
        this.groupToggle = Globals.env.getTemplate("templates/mdb/group-toggle.njk", compileNow);
        this.barTooltip = Globals.env.getTemplate("templates/mdb/bar-tooltip.njk", compileNow);
        this.dateSliders = Globals.env.getTemplate("templates/mdb/date-sliders.njk", compileNow);
        this.emptyResults = Globals.env.getTemplate("templates/mdb/empty-results.njk", compileNow);
        this.serverError = Globals.env.getTemplate("templates/mdb/server-error.njk", compileNow);
        this.commitHistory = Globals.env.getTemplate("templates/mdb/commit-history.njk", compileNow);
    }
}
