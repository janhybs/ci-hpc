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
