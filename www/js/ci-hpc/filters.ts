
class ConfigureViewFilters {
  static filterCommitSqueeze = {
    text: 'Commit squeeze value',
    key: 'squeeze',
    items: [
      {
        name: 'value', title: 'Commit', type: 'number',
        value: 1, min: 1, max: 10,
        format: 'Squeeze <span class="text code text-monospace"></span> commit(s) together',
        desc: 'This options is usefull when you have plenty of <code>commits</code> but have only couple of ' +
          '<code>repetitions</code> per commit. Higher value will increase performace but it can also ' +
          'conceal potential problem',
      },
    ]
  };

  static filterSeries = {
    text: 'Options',
    desc: 'Turn off additional series to save space and computing time <br />' +
      '<em>At least one option must be checked for chart to be displayed.</em>',
    items: [
      {
        text: 'show mean',
        name: 'show-mean',
        style: 'predefined',
        checked: false,
        desc: 'If checked, will display basic <strong>mean</strong> ' +
          'line chart.'
      },
      {
        text: 'show median',
        name: 'show-median',
        style: 'predefined',
        checked: true,
        desc: 'If checked, will display basic <strong>median</strong> ' +
          'line chart.'
      },
      {
        text: 'show std',
        name: 'show-stdbar',
        checked: false,
        desc: 'If checked, will also include <strong>area</strong> ' +
          'representing <code>standard deviation</code> of the observation.'
      },
      {
        text: 'show ci',
        name: 'show-ci',
        checked: true,
        desc: 'If checked, will also include <strong>area</strong> ' +
          'representing <code>95 % confidence interval</code> of the observation.'
      },
      {
        text: 'show errorbar',
        name: 'show-errorbar',
        checked: true,
        desc: 'If checked, will also include <strong>error bar</strong> ' +
          'in range of <code>mean &pm; 2.5%</code>.'
      },
      {
        text: 'show boxplot',
        name: 'show-boxplot',
        checked: false,
        desc: 'If checked, will also include <strong>box-and-whisker plot</strong> ' +
          'depicting groups of numerical data through their <code>quartiles</code>.<br /> ' +
          'Note that this option may slow down CI-HPC performance.'
      },
    ]
  };

  static filterMode = {
    text: 'View mode',
    key: 'mode',
    desc: 'Choose the display mode',
    radio: true,
    items: [
      {
        text: 'time series',
        name: 'time-series',
        checked: true,
        desc: 'If checked, the charts will display how the duration changes in time.'
      },
      {
        text: 'scale view',
        name: 'scale-view',
        checked: false,
        desc: 'If checked, the charts will display scaling (weak/strong) for each commit.'
      },
    ]
  }

  static filterGroupBy(fields) {
    return [
    {
      text: 'test-name',
      name: fields['problem.test'],
      style: 'predefined',
      checked: true,
      desc: '[auto option] if checked, will split the results into groups' +
        'based on test name'
    },
    {
      text: 'commit',
      name: fields['git.commit'],
      checked: true,
      style: 'predefined',
      desc: '[auto option] if checked, will split the results into groups' +
        'based on COMMIT value each group will have its own chart.'
    },
    {
      text: 'size',
      name: fields['problem.size'],
      style: 'predefined',
      checked: true,
      desc: '[auto option] if checked, will split the results into groups' +
        'based on SIZE value each group will have its own chart.'
    },
    {
      text: 'cpus',
      name: fields['problem.cpu'],
      style: 'predefined',
      checked: true,
      desc: '[auto option] if checked, will split the results into groups' +
        'based on CPU value each group will have its own chart.'
    }];
  }

}
