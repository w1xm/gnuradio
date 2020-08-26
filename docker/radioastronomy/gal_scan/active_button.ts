import {Button, ButtonView} from "models/widgets/button"
import {classes} from "core/dom"
import * as p from "core/properties"

import {bk_active} from "styles/mixins"

export class ActiveButtonView extends ButtonView {
  model: ActiveButton

  connect_signals(): void {
    super.connect_signals()
    this.connect(this.model.properties.active.change, () => this._update_active())
  }

  render(): void {
    super.render()
    this._update_active()
  }

  protected _update_active(): void {
    classes(this.button_el).toggle(bk_active, this.model.active)
  }
}

export namespace ActiveButton {
  export type Attrs = p.AttrsOf<Props>

  export type Props = Button.Props & {
    active: p.Property<boolean>
  }
}

export interface ActiveButton extends ActiveButton.Attrs {}

export class ActiveButton extends Button {
  properties: ActiveButton.Props
  __view_type__: ActiveButtonView

  constructor(attrs?: Partial<Button.Attrs>) {
    super(attrs)
  }

  static init_ActiveButton() {
    this.prototype.default_view = ActiveButtonView

    this.define<ActiveButton.Props>({
      active: [ p.Boolean, false ],
    })
  }
}
