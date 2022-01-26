(function($) {
"use strict";

var sensorTemplate = createSensorTemplate();

$.widget('ui.onresize', {
    _create: function() {
        var self = this;
        var el = this.element[0];

        if (this.element.css('position') === 'static') {
            this.element.css('position', 'relative');
        }
        
        this._emitting = false;
        this._sensor = sensorTemplate.clone().appendTo(this.element);
        this._sensors = {
            scroll: this._sensor.find('> :first')[0],
            expand: this._sensor.find('> :first > :first')[0],
            expandChild: this._sensor.find('> :first > :first > :first')[0],
            contract: this._sensor.find('> :first > :last')[0]
        };
        this._previousSize = {
            width: -1,
            height: -1
        };
        
        if (el.attachEvent) {
            this._handler = function() {
                self._onResize();
            };

            el.attachEvent('onresize', this._handler);
        } else {
            this._handler = function() {
                self._resetSensor();
                self._onResize();

                return false;
            };

            this._sensors.scroll.addEventListener('scroll', this._handler, true);
            this._resetSensor();
        }

        this.element.on('resize', function() {
            if (!self._emitting) {
                self._checkSize();
            }
        });
        
        if (this.options.resize) {
            this.element.on('resize', this.options.resize);
        }
    },
    _destroy: function() {
        var el = this.element[0];

        if (el.attachEvent) {
            el.detachEvent('onresize', this._handler);
        } else {
            this._sensors.scroll.removeEventListener('scroll', this._handler);
        }

        this._sensor.remove();
        this._sensor = null;
        this._sensors = null;
        this._handler = null;
    },
    _setOption: function(key, value) {
        if (key === 'resize') {
            if (this.options.resize) {
                this.element.off('resize', this.options.resize);
            }
            
            if (value) {
                this.element.on('resize', value);
            }
        }
        
        this._super(key, value);
    },
    _resetSensor: function() {
        this._sensors.contract.scrollLeft = this._sensors.contract.scrollWidth;
        this._sensors.contract.scrollTop = this._sensors.contract.scrollHeight;
        this._sensors.expandChild.style.width = this._sensors.expand.offsetWidth + 1 + 'px';
        this._sensors.expandChild.style.height = this._sensors.expand.offsetHeight + 1 + 'px';
        this._sensors.expand.scrollLeft = this._sensors.expand.scrollWidth;
        this._sensors.expand.scrollTop = this._sensors.expand.scrollHeight;
    },
    _onResize: function() {
        if (this._checkSize()) {
            this._emitting = true;
            this.element.trigger('resize');
            this._emitting = false;
        }
    },
    _checkSize: function() {
        var size = {
            height: this.element.outerHeight(),
            width: this.element.outerWidth()
        };

        if (size.height !== this._previousSize.height || size.width !== this._previousSize.width) {
            this._previousSize = size;
            return true;
        } else {
            return false;
        }
    }
});

var _onresize = $.fn.onresize;
$.fn.onresize = function(options) {
    if (options instanceof Function) {
        options = { resize: options };
    }
    
    return _onresize.call(this, options);
};

function createSensorTemplate() {
    var el = $('<div><div><div><div></div></div><div><div></div></div></div></div>');

    el.css({
        position: 'absolute',
        margin: 0,
        padding: 0,
        border: 0,
        top: 0,
        left: 0,
        bottom: 'auto',
        right: 'auto',
        overflow: 'hidden',
        height: '100%',
        width: '100%',
        visibility: 'hidden',
        opacity: 0
    })
    .children().css({
        position: 'absolute',
        margin: 0,
        padding: 0,
        border: 0,
        top: 0,
        left: 0,
        bottom: '-50px',
        right: '-50px',
        overflow: 'hidden',
        height: 'auto',
        width: 'auto'
    })
    .children().css({
        position: 'absolute',
        margin: 0,
        padding: 0,
        border: 0,
        top: 0,
        left: 0,
        bottom: 'auto',
        right: 'auto',
        overflow: 'auto',
        height: '100%',
        width: '100%'
    })
    .children().css({
        position: 'absolute',
        margin: 0,
        padding: 0,
        border: 0,
        top: 0,
        left: 0,
        bottom: 'auto',
        right: 'auto',
        overflow: 'hidden',
        height: '200%',
        width: '200%'
    });
    
    return el;
}
}(window.jQuery));