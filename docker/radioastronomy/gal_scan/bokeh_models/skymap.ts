// -*- mode: typescript; typescript-indent-level: 2 -*-
import {LayoutDOM, LayoutDOMView} from "@bokehjs/models/layouts/layout_dom"
import {LayoutItem} from "@bokehjs/core/layout"
import {Tap} from "@bokehjs/core/bokeh_events"
import * as p from "@bokehjs/core/properties"

declare namespace S {
  class VirtualSky {
    resize(): void
    addPointer(OPTIONS: object): number
    col: any
    highlight: (i: number) => void
    setLatitude(latitude: number): void
    setLongitude(longitude: number): void
    advanceTime(): void
    pointers: Array<S.pointer>
    azel2radec(az: number, el: number): S.radec
    radec2xy(ra: number, dec: number): S.xy
    draw(): void
    projection: S.projection
    d2r: number
    wide: number
    tall: number
    az_off: number
    ctx: CanvasRenderingContext2D
  }

  function virtualsky(OPTIONS: any): VirtualSky

  interface projection {
    title: string,
    azel2xy(az: number, el: number, w: number, h: number): S.xy
    xy2azel(x: number, y: number, w: number, h: number): [number, number]
    polartype: boolean
    atmos: boolean
    fullsky: boolean
  }

  interface event {
    x: number
    y: number
  }

  interface pointer {
    ra: number
    dec: number
    colour: any
    d: any
  }

  interface radec {
    ra: number
    dec: number
  }

  interface xy {
    x: number
    y: number
    el?: number
  }
}

// To create custom model extensions that will render on to the HTML canvas
// or into the DOM, we must create a View subclass for the model.
//
// In this case we will subclass from the existing BokehJS ``LayoutDOMView``
export class SkymapView extends LayoutDOMView {
  model: Skymap

  private _planetarium: S.VirtualSky

  private _pointerStatus: number
  private _pointerTarget: number

  render(): void {
    super.render()

    this.el.id = "skymap-" + this.model.id

    const view = this;
    this._planetarium = S.virtualsky({
      'id': this.el.id,
      'projection': 'stereo',
      'fov': 45,
      'az': 0, // TODO: get current value?
      'live': true,
      'showplanets': true,
      'showstarlabels': true,
      'gridlines_az': true,
      'gridlines_gal': true,
      'showgalaxy': true,
      'mouse': false,
      'objects': 'https://slowe.github.io/VirtualSky/messier.json',
      'callback': {
	'click': function(this: S.VirtualSky, e: S.event) {
	  const azel = this.projection.xy2azel(e.x, e.y, this.wide, this.tall)
	  const az = (azel[0]/this.d2r+this.az_off) % 360
	  const el = azel[1]/this.d2r
	  console.log(az, el)
	  view.click(e, [az, el])
	},
      },
    })

    // setTimeout(this._planetarium.resize)

    this._pointerStatus = this._planetarium.addPointer({
      ra: 0,
      dec: 0,
      label: 'status',
      d: 1.5, // degrees
      colour: this._planetarium.col.pointers,
    })-1;
    this._pointerTarget = this._planetarium.addPointer({
      ra: 0,
      dec: 0,
      d: 10, // pixels
      label: 'target',
      colour: 'red',
    })-1;

    const pointerStatus = this._pointerStatus
    const pointerTarget = this._pointerTarget

    const oldHighlight = this._planetarium.highlight;
    this._planetarium.highlight = function(i) {
      const p = this.pointers[i];
      if (p.ra && p.dec) {
	const pos = this.radec2xy(p.ra*this.d2r, p.dec*this.d2r);
	if (i == pointerTarget) {
	  // Draw a crosshair
	  const c = this.ctx;
	  c.beginPath();
	  c.strokeStyle = p.colour;
	  c.moveTo(pos.x-p.d, pos.y);
	  c.lineTo(pos.x-1, pos.y);
	  c.moveTo(pos.x+1, pos.y);
	  c.lineTo(pos.x+p.d, pos.y);
	  c.moveTo(pos.x, pos.y-p.d);
	  c.lineTo(pos.x, pos.y-1);
	  c.moveTo(pos.x, pos.y+1);
	  c.lineTo(pos.x, pos.y+p.d);
	  c.stroke();
	} else if (i == pointerStatus) {
	  // Draw a circle
	  // TODO: let radius = Math.abs(pos.x-this.radec2xy((p.ra-(p.d/2))*this.d2r, p.dec*this.d2r).x);
	  let radius = 5
	  const c = this.ctx;
	  c.beginPath();
	  c.strokeStyle = p.colour;
	  c.arc(pos.x, pos.y, radius, 0, 2*Math.PI);
	  c.stroke();
	} else {
	  oldHighlight.call(this, i);
	}
      }
    };
  }

  private updateAzel(pointer: number, azel?: [number, number]): void {
    if (azel == undefined || azel[0] == undefined || azel[1] == undefined) {
      this._planetarium.pointers[pointer].ra = this._planetarium.pointers[pointer].dec = 0;
      this._planetarium.draw();
      return;
    }
    this._planetarium.az_off = azel[0]%360-180;
    let radec = this._planetarium.azel2radec(azel[0]*this._planetarium.d2r, azel[1]*this._planetarium.d2r);
    this._planetarium.pointers[pointer].ra = radec.ra;
    this._planetarium.pointers[pointer].dec = radec.dec;
    this._planetarium.resize();
    this._planetarium.draw();
  }

  connect_signals(): void {
    super.connect_signals()
    // this.connect(this.model.properties.latlon.change, () => {
    //   const latlon = this.model.latlon
    //   this._planetarium.setLatitude(latlon[0])
    //   this._planetarium.setLongitude(latlon[1])
    //   this._planetarium.advanceTime()
    // })
    // // Set a listener so that when the Bokeh data source has a change
    // // event, we can process the new data
    // this.connect(this.model.properties.azel.change, () => this.updateAzel(this._pointerStatus, this.model.azel))
    // this.connect(this.model.targetAzel.change, () => this.updateAzel(this._pointerTarget, this.model.targetAzel))
    this.connect(this.model.change, this._on_change)
  }

  private _on_change(): void {
    const latlon = this.model.latlon
    if (latlon != undefined) {
      this._planetarium.setLatitude(latlon[0])
      this._planetarium.setLongitude(latlon[1])
      this._planetarium.advanceTime()
    }
    this.updateAzel(this._pointerStatus, this.model.azel)
    this.updateAzel(this._pointerTarget, this.model.targetAzel)
  }

  get child_models(): LayoutDOM[] {
    return []
  }

  _update_layout(): void {
    this.layout = new LayoutItem()
    this.layout.set_sizing(this.box_sizing())
    this._on_change()
    this._planetarium.resize()
  }

  click(e: S.event, azel: [number, number]): void {
    this.model.trigger_event(new Tap(e.x, e.y, azel[0], azel[1]))
  }
}

// We must also create a corresponding JavaScript BokehJS model subclass to
// correspond to the python Bokeh model subclass. In this case, since we want
// an element that can position itself in the DOM according to a Bokeh layout,
// we subclass from ``LayoutDOM``
export namespace Skymap {
  export type Attrs = p.AttrsOf<Props>

  export type Props = LayoutDOM.Props & {
    latlon: p.Any
    azel: p.Any
    targetAzel: p.Any
  }
}

export interface Skymap extends Skymap.Attrs {}

export class Skymap extends LayoutDOM {
  properties: Skymap.Props
  __view_type__: SkymapView
  static __module__ = "bokeh_models"

  constructor(attrs?: Partial<Skymap.Attrs>) {
    super(attrs)
  }

  static init_Skymap() {
    // This is usually boilerplate. In some cases there may not be a view.
    this.prototype.default_view = SkymapView

    // The @define block adds corresponding "properties" to the JS model. These
    // should basically line up 1-1 with the Python model class. Most property
    // types have counterparts, e.g. ``bokeh.core.properties.String`` will be
    // ``p.String`` in the JS implementatin. Where the JS type system is not yet
    // as rich, you can use ``p.Any`` as a "wildcard" property type.
    this.define<Skymap.Props>({
      latlon: [p.Any],
      azel: [p.Any],
      targetAzel: [p.Any],
    })
  }
}
