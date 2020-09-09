import {DataTable, DataTableView} from "@bokehjs/models/widgets/tables/data_table"
import {TableColumn, ColumnType, Item} from "@bokehjs/models/widgets/tables/table_column"
import {keys, to_object} from "@bokehjs/core/util/object"
import {uniqueId} from "@bokehjs/core/util/string"
import {CellCssStylesHash, Formatter} from "@bokeh/slickgrid"
import {CellMenu} from "@bokeh/slickgrid/plugins/slick.cellmenu"
// @ts-ignore
import cellmenu_css from "./slick.cellmenu.css"
import * as p from "@bokehjs/core/properties"

export class SortedDataTableView extends DataTableView {
  model: SortedDataTable

  updateGrid(): void {
    super.updateGrid()
    if (this.model.highlight_field) {
      const all = this.data.getLength() < 1 ? {} : to_object(
	new Map(keys(this.data.getItem(0)).map(k => [k, "highlight"])))
      const rows: CellCssStylesHash = {}
      Array.from(this.data.getItems().entries()).filter(([_,v]) => v[this.model.highlight_field]).forEach(([k,_]) => rows[k] = all)
      this.grid.setCellCssStyles(
	"highlight",
	rows
      )
    }
  }

  styles(): string[] {
    return [...super.styles(), cellmenu_css]
  }

  render(): void {
    super.render()
    const cellMenuPlugin = new CellMenu({ hideMenuOnScroll: true})
    this.grid.registerPlugin(cellMenuPlugin);
    // TODO: cellMenuPlugin.onCommand.subscribe(function (e, args) {})
    const columns = this.grid.getColumns()
    const to_sort = [{
      sortCol: {
        field: columns[1].field,
      },
      sortAsc: this.model.sort_ascending,
    }]
    this.data.sort(to_sort)
    this.grid.setSortColumn(columns[1].id || "", false)
    this.grid.invalidate()
    this.updateSelection()
    this.grid.render()
    this.model.update_sort_columns(to_sort)
  }
}

export namespace SortedDataTable {
  export type Attrs = p.AttrsOf<Props>
  export type Props = DataTable.Props & {
    highlight_field: p.Property<string>
    sort_ascending: p.Property<boolean>
  }
}

export interface SortedDataTable extends SortedDataTable.Attrs {
}

export class SortedDataTable extends DataTable {
  properties: SortedDataTable.Props
  __view_type__: SortedDataTableView
  static __module__ = "bokeh_models"

  static init_SortedDataTable(): void {
    this.prototype.default_view = SortedDataTableView
    this.define<SortedDataTable.Props>({
      highlight_field: [ p.String ],
      sort_ascending: [ p.Boolean, false ],
    })
    this.override({
      sortable: true,
    })
  }
}

export namespace ActionMenuColumn {
  export type Attrs = p.AttrsOf<Props>

  export type Props = TableColumn.Props & {
  }
}

export interface ActionMenuColumn extends ActionMenuColumn.Attrs {}

type CellMenuColumnType = ColumnType & {
  cellMenu: any,
}

export class ActionMenuColumn extends TableColumn {
  properties: ActionMenuColumn.Props
  static __module__ = "bokeh_models"

  constructor(attrs?: Partial<TableColumn.Attrs>) {
    super(attrs)
  }

  static init_ActionMenuColumn(): void {
    this.define<ActionMenuColumn.Props>({})
    this.override({
      width: 50,
    })
  }

  toColumn(): ColumnType {
    const actionFormatter: Formatter<Item> = (_row, _cell, _value, _columnDef, _dataContext) => {
      return `<div class="bk bk-btn bk-btn-default">Action <i class="fa fa-caret-down"></i></div>`;
    };
    const info: CellMenuColumnType = {
      id: uniqueId(),
      field: this.field,
      name: this.title ?? this.field,
      width: this.width,
      resizable: false,
      formatter: actionFormatter,
      cellMenu: {
	commandItems: [
	  { command: "cancel", title: "Cancel" },
	],
      },
      sortable: false,
    }
    return info
  }
}
