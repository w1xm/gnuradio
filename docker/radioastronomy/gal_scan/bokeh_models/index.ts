import {Knob} from "./knob"
import {Skymap} from "./skymap"
import {DownloadButton} from "./download_button"
import {UploadButton} from "./upload_button"
import {ActiveButton} from "./active_button"
import {SortedDataTable} from "./sorted_data_table"

import {register_models} from "@bokehjs/base"

register_models({Knob, Skymap, DownloadButton, UploadButton, ActiveButton, SortedDataTable})
