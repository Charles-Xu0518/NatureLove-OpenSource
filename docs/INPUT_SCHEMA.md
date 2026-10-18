# 输入字段

WeChatDataAnalysis 的 `schemaVersion: 1` 导出可先用 `scripts/convert_wechatdataanalysis.py` 转换，具体命令见[获取记录说明](GETTING_RECORDS.md)。其他工具需按下表整理，TXT/ZIP 和微信加密备份不能直接作为输入。

接受 UTF-8 / UTF-8-BOM 编码的 JSON 或 CSV。JSON 可为记录数组，或带 `messages` 数组的对象。CSV 的每一行是一条记录。导出软件的复杂嵌套 JSON、原始 XML、数据库和媒体目录需要先转换。

| 标准字段 | 必需 | 含义及别名 |
|---|---|---|
| `timestamp` | 是 | ISO 时间，建议带时区；或 Unix 秒/毫秒。别名 `ts`、`datetime`、`time`、`create_time` |
| `sender` | 是 | 与配置中两个参与者的 `id` 对应；别名 `sender_id`。系统消息可用其他值 |
| `type` | 否 | `text`、`image`、`video`、`voice`、`sticker`、`call`、`file`、`link`、`location`、`system`、`other`；默认 `text`。别名 `render_type` |
| `text` | 否 | 字符串正文；别名 `content`。文字字符量只统计 `text` 类型；不拼接引用原文 |
| `id` | 建议 | 每条消息唯一字符串；别名 `source_message_id`、`server_id` |
| `duration_seconds` | 可选 | 非负有限秒数；语音别名 `voice_sec`，通话别名 `call_sec` |
| `call_id` | 通话建议 | 用于归并同一次通话的稳定会话标识；别名 `call_session_id`、`room_id`。空值与 `0` 不参与归并 |
| `call_type` | 可选 | 如 `audio` / `video`。同会话类型冲突归为 `mixed` |
| `sticker_id` | 可选 | 表情资源的稳定标识；别名 `emoji_md5`。用于共用种类统计 |
| `media_path` | 可选 | 预留本地附件引用。本版本不复制、恢复、转写或播放附件 |

类型别名：`emoji → sticker`，`voip → call`，`quote → text`，`picture → image`，`audio → voice`。未知类型归 `other`，而未知的非系统发送者会报错，避免把群聊当成双人档案。

没有时区的 ISO 时间按配置的 `timezone` 解释。保留原导出时区通常更可靠。长消息标识请导出为字符串；工具无法恢复上游软件已经丢失的整数精度。

显式 ID 相同且记录一致时去重，并记录数量；同 ID 内容冲突会停止。没有 ID 的记录不按内容猜测去重，避免删除本来就重复发送的话。

通话提示可以在双方各出现一次。只有有效会话标识才能建立独立通话；没有标识的提示不直接增加独立次数。重复时长一致时只累计一次，全部缺失或相互冲突时保持缺失。记录的发送方向不解释为主叫身份。

转换后可先用少量合成/匿名化样本核对字段。原始导出、转换产物和真实配置放在 `private/`、`data/` 或默认忽略的 `config.local.json`，不要加入发布清单。
