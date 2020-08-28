import {DataTable, DataTableView} from "@bokehjs/models/widgets/tables/data_table"
import * as p from "@bokehjs/core/properties"

export class SortedDataTableView extends DataTableView {
  model: SortedDataTable

  render(): void {
    super.render()
    this.grid.autosizeColumns()
    const columns = this.grid.getColumns()
    const to_sort = [{
      sortCol: {
        field: columns[1].field,
      },
      sortAsc: false,
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
  export type Props = DataTable.Props
}

export interface SortedDataTable extends SortedDataTable.Attrs {
}

export class SortedDataTable extends DataTable {
  properties: SortedDataTable.Props
  __view_type__: SortedDataTableView
  static __module__ = "bokeh_models"

  static init_SortedDataTable(): void {
    this.prototype.default_view = SortedDataTableView
    this.override({
      sortable: true,
    })
  }
}
