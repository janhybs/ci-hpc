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
