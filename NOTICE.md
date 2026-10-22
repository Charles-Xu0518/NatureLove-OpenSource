# Methods, dependencies and distribution

Nature Love is created and maintained by Zhiheng Xu. This repository contains its own analysis implementation, configurable example dictionaries and report templates, released under the project's MIT license.

Scientific method references:

- Monroe, Colaresi & Quinn (2008), informative-prior weighted word contrasts: https://doi.org/10.1093/pan/mpn018
- Niederhoffer & Pennebaker (2002), linguistic style matching: https://doi.org/10.1177/026192702237953

The small Chinese function-word example is not the validated LIWC instrument. Statistical formulas and descriptive methods are not claims that the present implementation reproduces any published study's findings.

Dependencies retain their own licenses; installation obtains them through the Python package manager. No dependency source is vendored. TeX Gyre and Fandol fonts are resolved from the user's TeX installation, not copied into this repository.

No proprietary character artwork, celebrity photographs, brand assets, private correspondence, private aggregate results, database keys, local skill text, or real manuscript is part of this source distribution. Default ribbon artwork is drawn by the package. User-provided illustrations and inputs remain the user's responsibility and are excluded from the release file list.

Nature Love is a community commemorative project, not a Nature Portfolio publication or affiliated product.

The optional WeChatDataAnalysis converter independently maps the schemaVersion 1 JSON fields described by that project's export implementation: https://github.com/LifeArchiveProject/WeChatDataAnalysis/blob/main/src/wechat_decrypt_tool/chat_export_service.py. It does not include the upstream exporter or its database-access code.
