declare module "@bokeh/slickgrid/plugins/slick.cellmenu" {
  export interface CellMenuOptions extends Slick.PluginOptions {
    hideMenuOnScroll?: boolean
  }

  export class CellMenu<T extends Slick.SlickData> extends Slick.Plugin<T> {
    constructor(options?: CellMenuOptions)
  }
}
