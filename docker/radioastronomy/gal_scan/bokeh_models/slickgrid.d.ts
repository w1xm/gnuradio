declare module "@bokeh/slickgrid/plugins/slick.cellmenu" {
  export interface CellMenuOptions extends Slick.PluginOptions {
    hideMenuOnScroll?: boolean
  }

  export class CellMenu<T extends Slick.SlickData> extends Slick.Plugin<T> {
    constructor(options?: CellMenuOptions)
  }

  export interface Menu<T> {
    commandTitle?: string
    commandItems?: Array<MenuItem<T>>
    optionTitle?: string
    optionItems?: Array<MenuItem<T>>
    hideCloseButton?: boolean
    hideCommandSection?: boolean
    hideMenuOnScroll?: boolean
    hideOptionSection?: boolean
    maxHeight?: number | string
    width?: number | string
    autoAdjustDrop?: boolean
    autoAdjustDropOffset?: number
    autoAlignSide?: boolean
    autoAlignSideOffset?: number
    menuUsabilityOverride?: Function
  }

  export interface MenuItem<T> {
    action?: (e: DOMEvent, args: CallbackArgs<T>) => void
    command?: any
    option?: any
    title?: string
    divider?: boolean
    disabled?: boolean
    tooltip?: string
    cssClass?: string
    iconCssClass?: string
    textCssClass?: string
    iconImage?: string
    itemVisibilityOverride?: Function
    itemUsabilityOverride?: Function
  }

  export interface CallbackArgs<T> {
    cell: number
    row: number
    grid: Slick.Grid<T>
    command: any
    item: MenuItem<T>
    column: Slick.Column<T>
    dataContext: T
  }
}
