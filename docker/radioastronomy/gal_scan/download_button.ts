import {Button, ButtonView} from "models/widgets/button"
import {CallbackLike0} from "models/callbacks/callback"
import * as p from "core/properties"

export class DownloadButtonView extends ButtonView {
  model: DownloadButton

  private clickElement(node: HTMLElement): void {
    try {
      node.dispatchEvent(new MouseEvent('click'))
    } catch (e) {
      var evt = document.createEvent('MouseEvents')
      evt.initMouseEvent('click', true, true, window, 0, 0, 0, 80,
                         20, false, false, false, false, 0, null)
      node.dispatchEvent(evt)
    }
  }

  click(): void {
    const file = new File([this.model.data.execute(this.model)], this.model.filename, {type: this.model.mime_type})
    const URL = window.URL || window.webkitURL
    const a = document.createElement('a')
    a.download = file.name
    a.rel = 'noopener'
    a.href = URL.createObjectURL(file)
    setTimeout(() => URL.revokeObjectURL(a.href), 4E4)
    setTimeout(() => this.clickElement(a), 0)
  }
}

export namespace DownloadButton {
  export type Attrs = p.AttrsOf<Props>

  export type Props = Button.Props & {
    data: p.Property<CallbackLike0<DownloadButton, string>>
    filename: p.Property<string>
    mime_type: p.Property<string>
  }
}

export interface DownloadButton extends DownloadButton.Attrs {}

export class DownloadButton extends Button {
  properties: DownloadButton.Props
  __view_type__: DownloadButtonView

  constructor(attrs?: Partial<Button.Attrs>) {
    super(attrs)
  }

  static init_DownloadButton() {
    this.prototype.default_view = DownloadButtonView
    this.define<DownloadButton.Props>({
      data: [ p.Any ],
      filename: [ p.String, "data.bin" ],
      mime_type: [ p.String, "application/octet-stream" ],
    })
  }
}
