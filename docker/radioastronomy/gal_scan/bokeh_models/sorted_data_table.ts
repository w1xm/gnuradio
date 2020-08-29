import {DataTable, DataTableView} from "@bokehjs/models/widgets/tables/data_table"
import {keys, to_object} from "@bokehjs/core/util/object"
import {CellCssStylesHash} from "@bokeh/slickgrid"
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

  render(): void {
    super.render()
    this.grid.autosizeColumns()
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
