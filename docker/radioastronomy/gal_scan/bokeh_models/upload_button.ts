import {bk_btn, bk_btn_group, bk_btn_type} from "@bokehjs/styles/buttons"
import {FileInput, FileInputView} from "@bokehjs/models/widgets/file_input"
import {div, label} from "@bokehjs/core/dom"
import {ButtonType} from "@bokehjs/core/enums"
import * as p from "@bokehjs/core/properties"
// @ts-ignore
import upload_button_css from "./upload_button.css"

export class UploadButtonView extends FileInputView {
  model: UploadButton

  protected labelEl: HTMLLabelElement
  protected groupEl: HTMLElement

  private static _id_seq = 0

  styles(): string[] {
    return [...super.styles(), upload_button_css]
  }

  render(): void {
    super.render()
    if (!this.dialogEl.id) {
      this.dialogEl.id = this.model.name || ("upload-button-" + (UploadButtonView._id_seq++))
    }
    this.dialogEl.className = "visually-hidden"
    if (this.labelEl == null) {
      this.labelEl = label({'for': this.dialogEl.id, class: ["upload-button", bk_btn, bk_btn_type(this.model.button_type)]}, this.model.label)
    }
    if (this.groupEl == null) {
      this.groupEl = div({class: bk_btn_group}, this.labelEl)
      this.el.appendChild(this.groupEl)
    }
    this.labelEl.style.width = this.dialogEl.style.width
  }
}

export namespace UploadButton {
  export type Attrs = p.AttrsOf<Props>

  export type Props = FileInput.Props & {
    label: p.Property<string>
    button_type: p.Property<ButtonType>
  }
}

export interface UploadButton extends UploadButton.Attrs {}

export class UploadButton extends FileInput {
  properties: UploadButton.Props
  __view_type__: UploadButtonView
  static __module__ = "bokeh_models"

  constructor(attrs?: Partial<FileInput.Attrs>) {
    super(attrs)
  }

  static init_UploadButton() {
    this.prototype.default_view = UploadButtonView
    this.define<UploadButton.Props>({
      label: [ p.String, "Upload file" ],
      button_type: [ p.ButtonType, "default" ],
    })
  }
}
