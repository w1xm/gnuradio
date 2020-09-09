import {DataTable, DataTableView} from "@bokehjs/models/widgets/tables/data_table"
import {TableColumn, ColumnType, Item} from "@bokehjs/models/widgets/tables/table_column"
import {CallbackLike1} from "@bokehjs/models/callbacks/callback"
import {Class} from "@bokehjs/core/class"
import {keys, to_object} from "@bokehjs/core/util/object"
import {uniqueId} from "@bokehjs/core/util/string"
import {isString} from "@bokehjs/core/util/types"
import {BokehEvent, ModelEvent, JSON} from "@bokehjs/core/bokeh_events"
import {CellCssStylesHash, Formatter} from "@bokeh/slickgrid"
import {CellMenu, Menu, CallbackArgs} from "@bokeh/slickgrid/plugins/slick.cellmenu"
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
    menu: p.Property<(string | [string, string | CallbackLike1<ActionMenuColumn, {row: number, item: Item}>] | null)[]>
  }
}

export interface ActionMenuColumn extends ActionMenuColumn.Attrs {}

type CellMenuColumnType = ColumnType & {
  cellMenu: Menu<Item>
}

function event(event_name: string) {
  return function(cls: Class<BokehEvent>) {
    cls.prototype.event_name = event_name
  }
}

@event("action_menu_click")
export class ActionMenuClick extends ModelEvent {
  constructor(readonly item: string, readonly row: number, readonly value: any) {
    super()
  }
  protected _to_json(): JSON {
    const {item, row, value} = this
    return {...super._to_json(), item, row, value}
  }
}

export class ActionMenuColumn extends TableColumn {
  properties: ActionMenuColumn.Props
  static __module__ = "bokeh_models"

  constructor(attrs?: Partial<TableColumn.Attrs>) {
    super(attrs)
  }

  static init_ActionMenuColumn(): void {
    this.define<ActionMenuColumn.Props>({
      menu: [ p.Array, [] ],
    })
    this.override({
      width: 100,
    })
  }

  toColumn(): ColumnType {
    const actionFormatter: Formatter<Item> = (_row, _cell, _value, _columnDef, _dataContext) => {
      return `<div class="bk bk-btn bk-btn-default">Action ⬇</div>`;
    };
    const items = this.menu.map((item, i) => {
      if (item == null)
	return {divider: true}
      else {
	const title = isString(item) ? item : item[0]
	const valueOrCallback = isString(item) ? item : item[1]
	return {
	  command: valueOrCallback,
	  title: title,
	  action: (_event: DOMEvent, args: CallbackArgs<Item>) => this._item_click(i, args),
	}
      }
    })
    const info: CellMenuColumnType = {
      id: uniqueId(),
      field: this.field,
      name: this.title ?? this.field,
      width: this.width,
      resizable: false,
      formatter: actionFormatter,
      cellMenu: {
	commandItems: items,
      },
      sortable: false,
    }
    return info
  }
  protected _item_click(i: number, args: CallbackArgs<Item>): void {
    const item = this.menu[i]
    if (item != null) {
      const value_or_callback = isString(item) ? item : item[1]
      if (isString(value_or_callback)) {
	const value = args.column.field != null ? args.dataContext[args.column.field] : null
        this.trigger_event(new ActionMenuClick(value_or_callback, args.row, value))
      } else {
        value_or_callback.execute(this, {row: args.row, item: args.dataContext})
      }
    }
  }
}
