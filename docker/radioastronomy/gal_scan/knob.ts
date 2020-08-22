// -*- mode: typescript; typescript-indent-level: 2 -*-
import {HTMLBox, HTMLBoxView} from "models/layouts/html_box"
import {div, label} from "core/dom"
// Bokeh doesn't provide type information for css files
// @ts-ignore
import inputs_css from "styles/widgets/inputs.css"
// @ts-ignore
import knob_css from "./knob.css"
import {bk_input_group} from "styles/widgets/inputs"
import * as p from "core/properties"

// To create custom model extensions that will render on to the HTML canvas
// or into the DOM, we must create a View subclass for the model.
//
// In this case we will subclass from the existing BokehJS ``HTMLBoxView``
interface Place {
  element: HTMLElement
  text: Text
}
export class KnobView extends HTMLBoxView {
  model: Knob

  private _group_el: HTMLElement
  private _label_el: HTMLLabelElement

  private _places: Array<Place>
  private _marks: Array<HTMLElement>
  private _fixedMarks: Array<HTMLElement>

  initialize(): void {
    super.initialize()
    this._places = []
    this._marks = []
    this._fixedMarks = []
  }

  styles(): string[] {
    return [...super.styles(), inputs_css, knob_css]
  }

  render(): void {
    super.render()

    const clamp = (value: number, _direction: number) => {
      if (this.model.wrap) {
	while (value >= this.model.max) {
	  value -= (this.model.max-this.model.min);
	}
	while (value < this.model.min) {
	  value += (this.model.max-this.model.min);
	}
	return value;
      } else {
	if (this.model.max != undefined && value >= this.model.max) {
	  return this.model.max;
	}
	if (this.model.min != undefined && value < this.model.min) {
	  return this.model.min;
	}
	return value;
      }
    }

    const {title} = this.model
    this._label_el = label({style: {display: title.length == 0 ? "none" : ""}}, title)

    this._group_el = div({class: bk_input_group}, this._label_el)
    this.el.appendChild(this._group_el)

    const container = document.createElement('span');
    container.classList.add('widget-Knob-outer');

    this._group_el.append(container);

    const createPlace = (i: number, idx: number) => {
      if (i > 0 && i % 3 === 2 && this._places.length > 0) {
	const mark = container.appendChild(document.createElement("span"));
	mark.className = "knob-mark";
	mark.textContent = ",";
	//mark.style.visibility = "hidden";
	this._marks.unshift(mark);
	// TODO: make marks responsive to scroll events (doesn't matter which neighbor, or split in the middle, as long as they do something).
      }
      if (i === -1) {
	const mark = container.appendChild(document.createElement("span"));
	mark.className = "knob-mark";
	mark.textContent = ".";
	//mark.style.visibility = "hidden";
	this._fixedMarks.unshift(mark)
      }
      const digit = container.appendChild(document.createElement("span"));
      digit.className = "knob-digit";
      const digitText = digit.appendChild(document.createTextNode('0'));
      this._places[idx] = {element: digit, text: digitText};
      const scale = Math.pow(10, i);

      if (!this.model.writable) return;

      digit.tabIndex = -1;

      const spin = (direction: number) => {
	this.model.value = clamp(direction * scale + this.model.value, direction)
      }
      digit.addEventListener('wheel', event => {
	// TODO: deal with high-res/accelerated scrolling
	spin((event.deltaY || event.deltaX) > 0 ? 1 : -1);
	event.preventDefault();
	event.stopPropagation();
      }, {capture: true, passive: false});
      const focusNext = () => {
	if (idx > 0) {
	  this._places[idx - 1].element.focus();
	} else {
	  //digit.blur();
	}
      }
      const focusPrev = () => {
	if (idx < this._places.length - 1) {
	  this._places[idx + 1].element.focus();
	} else {
	  //digit.blur();
	}
      }
      digit.addEventListener('keydown', event => {
	switch (event.keyCode) {  // nominally poorly compatible, but best we can do
	  case 0x08: // backspace
	  case 0x25: // left
	    focusPrev();
	    break;
	  case 0x27: // right
	    focusNext();
	    break;
	  case 0x26: // up
	    spin(1);
	    break;
	  case 0x28: // down
	    spin(-1);
	    break;
	  default:
	    return;
	}
	event.preventDefault();
	event.stopPropagation();
      }, true);
      digit.addEventListener('keypress', event => {
	var ch = String.fromCharCode(event.charCode);
	var value = this.model.value;

	switch (ch) {
	  case '-':
	  case '_':
	    this.model.value = -Math.abs(value);
	    return;
	  case '+':
	  case '=':
	    this.model.value = Math.abs(value);
	    return;
	  case 'z':
	  case 'Z':
	    // zero all digits here and to the right
	    // | 0 is used to round towards zero
	    var zeroFactor = scale * 10;
	    this.model.value = ((value / zeroFactor) | 0) * zeroFactor;
	    return;
	  default:
	    break;
	}

	// TODO I hear there's a new 'input' event which is better for input-ish keystrokes, use that
	var input = parseInt(ch, 10);
	if (isNaN(input)) return;

	var negative = value < 0 || (value === 0 && 1/value === -Infinity);
	if (negative) { value = -value; }
	var currentDigitValue;
	if (scale === 1) {
	  // When setting last digit, clear anyT hidden fractional digits as well
	  currentDigitValue = (value / scale) % 10;
	} else {
	  currentDigitValue = Math.floor(value / scale) % 10;
	}
	value += (input - currentDigitValue) * scale;
	if (negative) { value = -value; }
	this.model.value = clamp(value, 0);

	focusNext();
	event.preventDefault();
	event.stopPropagation();
      });

      // remember last place for tabbing
      digit.addEventListener('focus', () => {
	this._places.forEach(other => {
	  other.element.tabIndex = -1;
	});
	digit.tabIndex = 0;
      }, false);

      // spin buttons
      digit.style.position = 'relative';
      [-1, 1].forEach(direction => {
	var up = direction > 0;
	var layoutShim = digit.appendChild(document.createElement('span'));
	layoutShim.className = 'knob-spin-button-shim knob-spin-' + (up ? 'up' : 'down');
	var button = layoutShim.appendChild(document.createElement('button'));
	button.className = 'knob-spin-button knob-spin-' + (up ? 'up' : 'down');
	button.textContent = up ? '+' : '-';
	function pushListener(event: Event) {
	  spin(direction);
	  event.preventDefault();
	  event.stopPropagation();
	}
	// Using these events instead of click event allows the button to work despite the auto-hide-on-focus-loss, in Chrome.
	button.addEventListener('touchstart', pushListener, {capture: true, passive: false});
	button.addEventListener('mousedown', pushListener, {capture: true, passive: false});
	//button.addEventListener('click', pushListener, false);
	// If in the normal tab order, its appearing/disappearing causes trouble
	button.tabIndex = -1;
      });
    }

    for (let i = (this.model.digits-1); i >= -this.model.decimals; i--) {
      createPlace(i, i+this.model.decimals);
    }

    if (this.model.unit != undefined) {
      const mark = container.appendChild(document.createElement("span"));
      mark.className = "knob-mark";
      mark.textContent = this.model.unit;
      this._fixedMarks.unshift(mark);
    }

    this._places[this._places.length - 1].element.tabIndex = 0; // initial tabbable digit
  }

  connect_signals(): void {
    super.connect_signals()
    this.connect(this.model.properties.title.change, () => {
      this._label_el.textContent = this.model.title
    })
    const {writable, digits, decimals, unit} = this.model.properties
    this.on_change([writable, digits, decimals, unit], () => this.render())
    const {min, max, value, disabled} = this.model.properties
    this.on_change([min, max, value, disabled], () => {
      const value = this.model.value;
      //console.log('externally changed to', value);
      const active = !this.model.disabled;
      let valueStr = new Intl.NumberFormat('en-US', { minimumFractionDigits: this.model.decimals, maximumFractionDigits: this.model.decimals, useGrouping: false }).format(value);
      if (valueStr === '0' && value === 0 && 1/value === -Infinity) {
	// allow user to see progress in entering negative values
	valueStr = '-0';
      }
      const valueStrDigits = valueStr.replace(".", "");
      const last = valueStrDigits.length - 1;
      for (let i = 0; i < this._places.length; i++) {
	const digit = valueStrDigits[last - i];
	this._places[i].text.data = digit || '0';
	this._places[i].element.classList[(digit && active) ? 'remove' : 'add']('knob-dim');
      }
      const numMarks = Math.floor((valueStrDigits.replace("-", "").length - 1 - 2) / 3);
      for (let i = 0; i < this._marks.length; i++) {
	this._marks[i].classList[(i < numMarks && active) ? 'remove' : 'add']('knob-dim');
      }
      for (let i = 0; i < this._fixedMarks.length; i++) {
	this._fixedMarks[i].classList[active ? 'remove' : 'add']('knob-dim');
      }
    })
  }
}

// We must also create a corresponding JavaScript BokehJS model subclass to
// correspond to the python Bokeh model subclass. In this case, since we want
// an element that can position itself in the DOM according to a Bokeh layout,
// we subclass from ``HTMLBox``
export namespace Knob {
  export type Attrs = p.AttrsOf<Props>

  export type Props = HTMLBox.Props & {
    title: p.Property<string>
    writable: p.Property<boolean>
    digits: p.Property<number>
    decimals: p.Property<number>
    max: p.Property<number>
    min: p.Property<number>
    value: p.Property<number>
    wrap: p.Property<boolean>
    unit: p.Property<string>
    active: p.Property<boolean>
  }
}

export interface Knob extends Knob.Attrs {}

export class Knob extends HTMLBox {
  properties: Knob.Props
  __view_type__: KnobView

  constructor(attrs?: Partial<Knob.Attrs>) {
    super(attrs)
  }

  static init_Knob() {
    // This is usually boilerplate. In some cases there may not be a view.
    this.prototype.default_view = KnobView

    this.define<Knob.Props>({
      title: [ p.String, "" ],
      writable: [ p.Boolean, false ],
      digits: [ p.Number, 3 ],
      decimals: [ p.Number, 3 ],
      max: [ p.Number ],
      min: [ p.Number ],
      value: [ p.Number, 0 ],
      wrap: [ p.Boolean, false ],
      unit: [ p.String ],
      active: [ p.Boolean, true ],
    })
  }
}
