# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**

> High cosine similarity nghĩa là hai vector gần cùng hướng, tức là hai câu hoặc hai đoạn văn có mức độ tương đồng ngữ nghĩa cao. Trong retrieval, score cosine càng cao thì khả năng chunk đó liên quan đến query càng lớn.

**Ví dụ HIGH similarity:**

- Sentence A: Tiki hoàn tiền sau 3 ngày làm việc kể từ khi kiện hàng tới nhà bán.
- Sentence B: Quy trình hoàn tiền được xử lý trong 3 ngày làm việc sau khi kiện hàng tới nhà bán.
- Tại sao tương đồng: Hai câu diễn đạt cùng một ý, cùng mốc thời gian và cùng ngữ cảnh hoàn tiền sau trả hàng.

**Ví dụ LOW similarity:**

- Sentence A: Tiki hoàn tiền bằng Tiki Xu trong 24 giờ.
- Sentence B: Dịch vụ TikiNOW giao nhanh trong 2 giờ.
- Tại sao khác: Một câu nói về hoàn tiền, câu còn lại nói về giao hàng nhanh nên chủ đề khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**

> Cosine similarity tập trung vào hướng của vector nên phù hợp hơn với text embeddings, vì điều quan trọng là mức độ giống nhau về ngữ nghĩa chứ không phải độ lớn tuyệt đối của vector. Khi embeddings đã được chuẩn hóa, cosine similarity cũng ổn định và dễ diễn giải hơn Euclidean distance.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính:* `step = chunk_size - overlap = 500 - 50 = 450`  
> Số chunks `= ceil((10000 - 500) / 450) + 1 = ceil(9500 / 450) + 1 = 22 + 1`
> *Đáp án:* `23 chunks`

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

> Nếu overlap tăng lên 100 thì `step = 400`, nên số chunk tăng thành `25`. Overlap lớn hơn giúp giữ ngữ cảnh tốt hơn giữa hai chunk liền kề, nhất là khi thông tin quan trọng nằm gần ranh giới chia chunk.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Customer Support Policy (E-commerce)

**Tại sao nhóm chọn domain này?**

> - Dễ kiếm doc (đổi trả, giao hàng, bảo hành, thanh toán…)
> - Có nhiều rule **rõ ràng + dễ sai**
> - RAG thể hiện rõ giá trị (retrieve đúng chunk hay không)

### Data Inventory


| #   | Tên tài liệu                                                                                        | Nguồn        | Số ký tự | Metadata đã gán                                                                                 |
| --- | --------------------------------------------------------------------------------------------------- | ------------ | -------- | ----------------------------------------------------------------------------------------------- |
| 1   | Chính sách hậu mãi: Đổi mới, trả hàng hoàn tiền và bảo hành sản phẩm                                | `data/1.md`  | 7277     | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |
| 2   | Chính sách đổi trả sản phẩm                                                                         | `data/2.md`  | 5567     | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |
| 3   | Các câu hỏi thường gặp về đổi trả                                                                   | `data/3.md`  | 4222     | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |
| 4   | Hướng dẫn đổi trả online                                                                            | `data/4.md`  | 1688     | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |
| 5   | Chính sách bảo hành tại Tiki như thế nào?                                                           | `data/5.md`  | 3035     | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |
| 6   | Tiki hiện đang hỗ trợ các phương thức thanh toán nào                                                | `data/6.md`  | 2976     | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |
| 7   | Làm thế nào để tôi có thể lưu và sử dụng mã coupon?                                                 | `data/7.md`  | 1262     | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |
| 8   | Dịch vụ giao hàng từ nước ngoài                                                                     | `data/8.md`  | 3237     | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |
| 9   | Dịch vụ giao hàng TikiNOW                                                                           | `data/9.md`  | 2244     | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |
| 10  | Tôi có thể yêu cầu giao theo thời gian cụ thể, giao vào chủ nhật hoặc trên lầu/phòng chung cư không | `data/10.md` | 927      | `source`, `extension`, `doc_title`, `doc_id`, `chunk_index`, `total_chunks`, `chunk_char_count` |


### Metadata Schema


| Trường metadata    | Kiểu    | Ví dụ giá trị                       | Tại sao hữu ích cho retrieval?                                                                    |
| ------------------ | ------- | ----------------------------------- | ------------------------------------------------------------------------------------------------- |
| `source`           | string  | `data/3.md`                         | Giúp trace lại chunk đang đến từ file nào để kiểm chứng kết quả retrieval và trích nguồn          |
| `extension`        | string  | `.md`                               | Giúp phân biệt loại tài liệu nếu corpus sau này có nhiều định dạng khác nhau                      |
| `doc_title`        | string  | `Các câu hỏi thường gặp về đổi trả` | Giúp nhanh chóng hiểu chủ đề của chunk và có thể dùng để lọc/rerank theo loại câu hỏi             |
| `doc_id`           | string  | `3`                                 | Giúp nhóm các chunk thuộc cùng một tài liệu, phục vụ filter và delete theo document               |
| `chunk_index`      | integer | `2`                                 | Giúp xác định vị trí chunk trong tài liệu gốc để đọc nối ngữ cảnh khi phân tích kết quả           |
| `total_chunks`     | integer | `9`                                 | Cho biết chunk đang ở tài liệu dài hay ngắn, hữu ích khi debug coverage của strategy chunking     |
| `chunk_char_count` | integer | `486`                               | Giúp theo dõi kích thước chunk thực tế và so sánh chất lượng retrieval giữa các cấu hình chunking |


---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:


| Tài liệu    | Strategy                         | Chunk Count | Avg Length | Preserves Context?                                   |
| ----------- | -------------------------------- | ----------- | ---------- | ---------------------------------------------------- |
| `data/1.md` | FixedSizeChunker (`fixed_size`)  | 17          | 475.12     | Trung bình, kích thước ổn định nhưng dễ cắt ngang ý  |
| `data/1.md` | SentenceChunker (`by_sentences`) | 9           | 806.67     | Tốt về mặt ngữ nghĩa, nhưng chunk khá dài            |
| `data/1.md` | RecursiveChunker (`recursive`)   | 24          | 301.71     | Tốt, giữ cấu trúc đoạn và tách linh hoạt             |
| `data/2.md` | FixedSizeChunker (`fixed_size`)  | 13          | 474.38     | Trung bình, đều kích thước nhưng có thể gãy nội dung |
| `data/2.md` | SentenceChunker (`by_sentences`) | 7           | 791.57     | Khá tốt về mạch câu, nhưng hơi dài cho retrieval     |
| `data/2.md` | RecursiveChunker (`recursive`)   | 13          | 426.31     | Tốt, cân bằng giữa độ dài và ngữ cảnh                |
| `data/3.md` | FixedSizeChunker (`fixed_size`)  | 10          | 467.20     | Trung bình, ổn định nhưng chưa tối ưu cho FAQ        |
| `data/3.md` | SentenceChunker (`by_sentences`) | 7           | 599.29     | Khá tốt, vì FAQ thường theo câu và đoạn ngắn         |
| `data/3.md` | RecursiveChunker (`recursive`)   | 11          | 382.00     | Tốt, chunk ngắn hơn và vẫn giữ được ý chính          |


### Strategy Của Tôi

**Loại:** SentenceChunker

**Mô tả cách hoạt động:**

> *Strategy này chia văn bản theo ranh giới câu bằng regex, sau đó gom nhiều câu liên tiếp thành một chunk dựa trên max_sentences_per_chunk. Cách làm này giúp mỗi chunk giữ được ý nghĩa tự nhiên hơn so với việc cắt cứng theo số ký tự. Với tài liệu FAQ và policy, nhiều thông tin quan trọng nằm trọn trong 1-3 câu liên tiếp, nên chunk theo câu giúp giảm tình trạng cắt ngang định nghĩa, điều kiện hoặc mốc thời gian. Ngoài ra, các chunk tạo ra vẫn khá dễ đọc và dễ kiểm tra thủ công khi đánh giá retrieval.*

**Tại sao tôi chọn strategy này cho domain nhóm?**

> *Tài liệu của nhóm chủ yếu là chính sách và câu hỏi thường gặp, nên thông tin thường nằm trong các câu hoặc đoạn ngắn rõ ràng. Chia theo câu giúp retrieval trả về các đoạn dễ đọc, dễ đối chiếu hơn, và giảm khả năng mất ngữ cảnh so với cắt cố định theo độ dài.*

**Code snippet (nếu custom):**

```python
# Không áp dụng vì mình dùng SentenceChunker có sẵn trong src/chunking.py
```

### So Sánh: Strategy của tôi vs Baseline


| Tài liệu    | Strategy                     | Chunk Count | Avg Length | Retrieval Quality?                                |
| ----------- | ---------------------------- | ----------- | ---------- | ------------------------------------------------- |
| `data/3.md` | best baseline (`recursive`)  | 11          | 382.00     | Tốt hơn ở retrieval vì chunk gọn và tập trung hơn |
| `data/3.md` | **của tôi** (`by_sentences`) | 7           | 599.29     | Khá tốt, dễ đọc và giữ ý trọn vẹn nhưng hơi dài   |


### So Sánh Với Thành Viên Khác


| Thành viên     | Strategy         | Retrieval Score (/10) | Điểm mạnh                                                 | Điểm yếu                                            |
| -------------- | ---------------- | --------------------- | --------------------------------------------------------- | --------------------------------------------------- |
| Lê Hồng Quân   | SentenceChunker  | 7 / 10                | Chunk dễ đọc, giữ ngữ nghĩa tự nhiên, hợp với FAQ/policy  | Một số chunk dài nên retrieval chưa luôn đứng top-1 |
| Phạm Thanh Lam | RecursiveChunker | 8/10                  | Cân bằng giữa độ dài và ngữ cảnh, thường mạnh ở retrieval | Sinh nhiều chunk hơn, khó kiểm tra thủ công hơn     |
| Linh           | FixedSizeChunker | 5                     | Dễ triển khai, chunk size ổn định                         | Dễ cắt ngang ý và làm mất ngữ cảnh                  |


**Strategy nào tốt nhất cho domain này? Tại sao?**

> Với domain chính sách và FAQ của Tiki, `RecursiveChunker` là strong baseline vì giữ được cấu trúc đoạn và thường cho chunk gọn hơn nên retrieval chính xác hơn. Tuy nhiên `SentenceChunker` vẫn là lựa chọn hợp lý khi ưu tiên chunk dễ đọc, tự nhiên và thuận tiện cho việc kiểm tra thủ công. Nếu tối ưu riêng cho chất lượng retrieve thì recursive có lợi thế hơn, còn nếu ưu tiên tính diễn giải và coherence thì sentence-based chunking khá phù hợp.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

`**SentenceChunker.chunk`** — approach:

> Mình dùng regex `(?<=[.!?])\s+` để tách câu theo dấu chấm, chấm hỏi, chấm than kèm khoảng trắng phía sau. Sau khi tách, mình `strip()` từng câu và loại bỏ phần tử rỗng để tránh sinh chunk lỗi khi văn bản có nhiều khoảng trắng hoặc xuống dòng. Cuối cùng các câu được gom theo `max_sentences_per_chunk` để mỗi chunk vẫn giữ được ý hoàn chỉnh.

`**RecursiveChunker.chunk` / `_split`** — approach:

> `RecursiveChunker` thử tách theo thứ tự separator từ lớn đến nhỏ như `\n\n`, `\n`, `.` , dấu cách, rồi cuối cùng mới fallback sang cắt cứng theo số ký tự. Base case là khi đoạn hiện tại đã ngắn hơn hoặc bằng `chunk_size`, hoặc khi đã hết separator thì chia theo lát cắt cố định. Cách này giúp ưu tiên giữ cấu trúc tự nhiên của tài liệu trước khi phải cắt nhỏ hơn.

### EmbeddingStore

`**add_documents` + `search`** — approach:

> `add_documents` chuẩn hóa mỗi `Document` thành một record gồm `id`, `content`, `metadata` và `embedding`, sau đó lưu vào ChromaDB nếu có hoặc fallback sang list trong bộ nhớ. `search` sẽ embed câu query rồi tính độ tương đồng với các embeddings đã lưu; ở nhánh in-memory, score được tính bằng dot product vì embeddings đang được chuẩn hóa. Kết quả cuối được sort giảm dần theo score và cắt theo `top_k`.

`**search_with_filter` + `delete_document`** — approach:

> `search_with_filter` filter metadata trước rồi mới chạy similarity search, vì nếu search xong mới filter thì có thể làm mất các candidate thật sự liên quan trong tập con mong muốn. `delete_document` xóa toàn bộ chunks có cùng `doc_id`, giúp loại bỏ trọn vẹn một tài liệu khỏi store. Cách làm này phù hợp với thiết kế metadata hiện tại vì mỗi chunk đều mang `doc_id` của tài liệu gốc.

### KnowledgeBaseAgent

`**answer`** — approach:

> `answer` hiện retrieve top-1 chunk rồi inject trực tiếp chunk đó vào prompt cùng với câu hỏi của user. Prompt yêu cầu mô hình trả lời bằng tiếng Việt, chỉ dựa trên context đã retrieve và phải thừa nhận khi context không đủ. Cách này giúp câu trả lời grounded hơn, dù trade-off là nếu top-1 sai thì agent cũng khó cứu được kết quả cuối.

### Test Results

```
# python -m unittest tests.test_solution -v

Ran 42 tests in 0.014s

OK
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)


| Pair | Sentence A                                                          | Sentence B                                                                               | Dự đoán | Actual Score | Đúng?    |
| ---- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------- | ------------ | -------- |
| 1    | Tiki hoàn tiền sau 3 ngày làm việc kể từ khi kiện hàng tới nhà bán. | Quy trình hoàn tiền được xử lý trong 3 ngày làm việc sau khi kiện hàng tới nhà bán.      | high    | 0.7906       | Đúng     |
| 2    | Nếu gửi hàng bảo hành về Tiki thì thời gian dự kiến là 15-30 ngày.  | Khách gửi bảo hành về Tiki sẽ nhận lại hàng sau 15 đến 30 ngày.                          | high    | 0.9219       | Đúng     |
| 3    | Đơn hàng quốc tế giao lại tối đa 3 lần và giữ kho 14 ngày.          | Hàng từ nước ngoài nếu giao không thành công sẽ được giao lại 3 lần rồi giữ kho 14 ngày. | high    | 0.7653       | Đúng     |
| 4    | Khách có thể hẹn lại thời gian giao hàng khác qua điện thoại.       | Tiki chưa hỗ trợ giao hàng vào đúng giờ cụ thể theo yêu cầu.                             | low     | 0.5050       | Một phần |
| 5    | Tiki hoàn tiền bằng Tiki Xu trong 24 giờ.                           | Dịch vụ TikiNOW giao nhanh trong 2 giờ.                                                  | low     | 0.5909       | Sai      |


**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**

> Điều bất ngờ nhất là cặp số 5 vẫn có cosine similarity khá cao dù một câu nói về hoàn tiền bằng Tiki Xu, còn câu kia nói về giao nhanh TikiNOW. Điều này cho thấy embedding thật không chỉ học từ các từ khóa bề mặt mà còn bị ảnh hưởng bởi bối cảnh chung của domain e-commerce, nên những câu cùng nằm trong ngữ cảnh dịch vụ Tiki vẫn có thể được kéo gần nhau hơn dự đoán. Ngược lại, cặp số 4 cũng cho score trung bình khá vì cả hai câu đều liên quan đến việc điều chỉnh thời gian giao hàng, dù ý nghĩa cuối cùng không hoàn toàn giống nhau.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)


| #   | Query                                                                                       | Gold Answer                                                                                                                                                                                                                                         |
| --- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Sau khi kiện trả hàng tới nhà bán thì bao lâu Tiki xử lý hoàn tiền?                         | Tiki hoàn tiền sau khi quy trình kiểm tra, đánh giá chất lượng sản phẩm đổi/trả hoàn tất; riêng phần xử lý này cần 3 ngày làm việc kể từ khi kiện hàng được chuyển tới nhà bán.                                                                     |
| 2   | Nếu tôi gửi sản phẩm bảo hành về Tiki thì bao lâu nhận lại?                                 | Nếu khách gửi hàng bảo hành về Tiki, thời gian bảo hành dự kiến là 15–30 ngày, chưa tính thời gian vận chuyển đi và về.                                                                                                                             |
| 3   | Đơn giao từ nước ngoài mà giao không thành công thì Tiki giao lại mấy lần, giữ kho bao lâu? | Với đơn giao từ nước ngoài, nếu giao không thành công thì Tiki hỗ trợ giao lại tối đa 03 lần; sau đó hàng được giữ tại kho Tiki 14 ngày. Nếu quá thời hạn đó khách không liên hệ nhận hàng thì Tiki tiến hành hoàn tiền qua đơn hàng.               |
| 4   | Muốn dùng Tiki Xu và mã giảm giá thì có điều kiện gì?                                       | Khách chỉ có thể dùng Tiki Xu khi có từ 1000 Xu trở lên; còn mỗi mã giảm giá chỉ dùng 1 lần trên 1 tài khoản.                                                                                                                                       |
| 5   | Tôi có thể yêu cầu giao vào giờ cụ thể hoặc hẹn lại chủ nhật không?                         | Sau khi đặt hàng thành công, Tiki sẽ thông báo thời gian giao dự kiến. Nếu thời điểm shipper liên hệ chưa phù hợp, khách có thể trao đổi qua điện thoại để hẹn lại thời gian giao khác, và nhân viên vận chuyển sẽ cố gắng hỗ trợ trong mức có thể. |


### Kết Quả Của Tôi

Lưu ý: sau khi đổi `main.py` sang `SentenceChunker`, cần chạy lại 5 benchmark queries để cập nhật chính xác top-1 chunk, score và agent answer. Bảng dưới đây ghi trạng thái đánh giá hiện tại và các nguồn dữ liệu dự kiến liên quan nhất theo corpus.

| #   | Query                                                                                       | Top-1 Retrieved Chunk (tóm tắt)                                                                                                       | Score                      | Relevant?           | Agent Answer (tóm tắt)                                                                 |
| --- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- | ------------------- | -------------------------------------------------------------------------------------- |
| 1   | Sau khi kiện trả hàng tới nhà bán thì bao lâu Tiki xử lý hoàn tiền?                         | Dự kiến chunk liên quan nhất nằm ở `data/3.md`, phần FAQ “Thời gian hoàn tiền” có nêu mốc xử lý 3 ngày làm việc                     | Cần chạy lại benchmark     | Có                  | Nếu retrieve đúng `data/3.md` thì agent có thể trả lời đúng mốc 3 ngày làm việc        |
| 2   | Nếu tôi gửi sản phẩm bảo hành về Tiki thì bao lâu nhận lại?                                 | Dự kiến chunk liên quan nhất nằm ở `data/5.md`, phần chính sách bảo hành có nêu mốc 15-30 ngày                                       | Cần chạy lại benchmark     | Có                  | Nếu retrieve đúng `data/5.md` thì agent có thể trả lời đúng mốc 15-30 ngày             |
| 3   | Đơn giao từ nước ngoài mà giao không thành công thì Tiki giao lại mấy lần, giữ kho bao lâu? | Dự kiến chunk liên quan nhất nằm ở `data/8.md`, có đầy đủ thông tin giao lại 03 lần và giữ kho 14 ngày                               | Cần chạy lại benchmark     | Có                  | Agent có thể trả lời khá đầy đủ nếu top-1 là chunk chính sách giao hàng quốc tế        |
| 4   | Muốn dùng Tiki Xu và mã giảm giá thì có điều kiện gì?                                       | Corpus hiện tại chỉ có thông tin rời rạc về Tiki Xu và coupon, chưa thấy đủ evidence cho điều kiện `1000 Xu` và `1 lần / 1 tài khoản` | Cần chạy lại benchmark     | Một phần / Không đủ | Agent nên trả lời không thể xác nhận đầy đủ từ corpus hiện tại                         |
| 5   | Tôi có thể yêu cầu giao vào giờ cụ thể hoặc hẹn lại chủ nhật không?                         | Dự kiến chunk liên quan nhất nằm ở `data/10.md`, nói không hỗ trợ giờ giao cụ thể nhưng có thể hẹn lại thời gian khác                | Cần chạy lại benchmark     | Có                  | Agent có thể trả lời đúng rằng không chọn giờ cụ thể nhưng có thể hẹn lại ở mức có thể |


**Bao nhiêu queries trả về chunk relevant trong top-3?** Cần cập nhật sau khi rerun 5 benchmark queries với SentenceChunker

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**

> Mình học được rằng chỉ thay đổi chunking strategy thôi cũng có thể làm top-k retrieval khác đi khá nhiều, dù dùng cùng một bộ tài liệu và cùng query. Đặc biệt, strategy thiên về giữ ngữ cảnh như recursive chunking thường giúp những query cần chi tiết cụ thể có kết quả tốt hơn. Điều này làm mình hiểu rõ hơn rằng data strategy quan trọng không kém model.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**

> Qua demo của nhóm khác, mình thấy metadata schema có thể tạo khác biệt lớn khi query cần lọc theo loại tài liệu hoặc tình huống nghiệp vụ. Một nhóm gắn metadata chi tiết hơn cho chủ đề và loại policy nên việc debug retrieval dễ hơn hẳn. Điều này cho mình thêm góc nhìn rằng retrieval tốt không chỉ đến từ embeddings mà còn từ cách tổ chức dữ liệu.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**

> Nếu làm lại, mình sẽ chuẩn hóa metadata theo `topic`, `doc_type` và `updated_at` thay vì chủ yếu dựa vào `source` và `doc_id`. Mình cũng sẽ tách riêng các FAQ ngắn và các policy dài để dùng chunking strategy khác nhau cho từng nhóm tài liệu. Ngoài ra, mình sẽ benchmark sớm hơn với 5 query chuẩn để phát hiện corpus nào còn thiếu evidence như trường hợp query về Tiki Xu và mã giảm giá.

---

## Tự Đánh Giá


| Tiêu chí                    | Loại    | Điểm tự đánh giá |
| --------------------------- | ------- | ---------------- |
| Warm-up                     | Cá nhân | 5 / 5            |
| Document selection          | Nhóm    | 9 / 10           |
| Chunking strategy           | Nhóm    | 12 / 15          |
| My approach                 | Cá nhân | 9 / 10           |
| Similarity predictions      | Cá nhân | 4 / 5            |
| Results                     | Cá nhân | 8 / 10           |
| Core implementation (tests) | Cá nhân | 30 / 30          |
| Demo                        | Nhóm    | 4 / 5            |
| **Tổng**                    |         | **81 / 100**     |

