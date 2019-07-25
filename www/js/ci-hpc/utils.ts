class DD {
  dict: object;

  constructor() {
    this.dict = {};
  }

  get(keys: string[]) {
    var o: object = this.dict;
    for (let key of keys) {
      if (o.hasOwnProperty(key)) {
        o = o[key]
      } else {
        return undefined;
      }
    }
    return o;
  }

  set(keys: string[], value: any) {
    var o: object = this.dict;
    for (let i = 0; i < keys.length - 1; i++) {
      var key: string = keys[i];
      if (!o.hasOwnProperty(key)) {
        o[key] = {};
      }
      o = o[key];
    }
    o[keys[keys.length - 1]] = value;
    return o;
  }
}


class Utils {

  static opts = {};

  static extendJQuery() {
    /**
      * Extends functionality of the jQuery's attr method.
      * If no arguments are passed, will return all attributes
      */
    (function(old) {
      $.fn.attr = function() {
        if (arguments.length === 0) {
          if (this.length === 0) {
            return null;
          }

          var obj = {};
          $.each(this[0].attributes, function() {
            if (this.specified) {
              obj[this.name] = this.value;
            }
          });
          return obj;
        }

        return old.apply(this, arguments);
      };
    })($.fn.attr);
  }

  static grabOptions() {
    var opts = new DD();

    $('#cihpc-option-holder input[type="checkbox"]').each(function(index, item) {
      var isChecked = $(this).is(':checked');
      var optGroup = $(this).data('key');
      if (optGroup) {
        opts.set([optGroup, $(this).attr('name')], isChecked);
      } else {
        opts.set([$(this).attr('name')], isChecked);
      }
    });

    $('#cihpc-option-holder input[type="radio"]:checked').each(function(index, item) {
      var optGroup = $(this).data('key');
      if (optGroup) {
        opts.set([optGroup, $(this).attr('name')], $(this).val());
      } else {
        opts.set([$(this).attr('name')], $(this).val());
      }
    });

    $('#cihpc-option-holder .cihpc-slider input').each(function(index, item) {
      var optGroup = $(this).data('key');
      if (optGroup) {
        opts.set([optGroup, $(this).attr('name')], $(this).val());
      } else {
        opts.set([$(this).attr('name')], $(this).val());
      }
    });

    console.log(opts.dict);
    return opts.dict;
  };

  static updateOptionGroups = function() {
    var mode = $('#form-mode input:checked').val();
    var cls1 = 'disabled btn-light',
      cls2 = 'btn-primary';

    if (mode == 'time-series') {
      $('#groupby-commit').prop('disabled', true);
      $('#groupby-cpus').prop('disabled', false);
      $('#groupby-size').prop('disabled', false);

    } else if (mode == 'scale-view') {
      $('#groupby-commit').prop('disabled', false);
      $('#groupby-cpus').prop('disabled', true);
      $('#groupby-size').prop('disabled', true);
    }
  };

  static createDateSliders = function() {
    $('.cihpc-slider').each(function() {
      var $this = $(this);
      var $text = $this.find('.text');
      var $value = $this.find('.value');
      var min, max;

      if ($this.data('type') == 'number') {
        var defval = $value.data('default');
        if (defval) {
          $value.val(defval);
        }

        $value.on('input', function() {
          $text.html((<HTMLInputElement>this).value);
        });
        $value.trigger('input');

      } else if ($this.data('type') == 'date') {
        if (!$value.attr('min')) {
          min = window.moment().subtract(5, 'months').format('X')
          $value.attr('min', min);
        }
        if (!$value.attr('max')) {
          max = (new Date().getTime() / 1000).toFixed();
          $value.attr('max', max);
        }
        var defval = $value.data('default');
        if (defval) {
          if (defval === 'min') {
            $value.val(min);
          } else if (defval === 'max') {
            $value.val(max);
          } else {
            $value.val(defval);
          }
        }

        $value.on('input', function() {
          var m = window.moment((<HTMLInputElement>this).value, 'X');
          var abs = m.format('DD.MM YYYY');
          var rel = m.fromNow();
          $text.html(abs + ' <small>' + rel + '</small>');
        });
        $value.trigger('input');
      }
    });
  };


}
