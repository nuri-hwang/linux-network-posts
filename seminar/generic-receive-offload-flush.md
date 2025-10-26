---
marp: true
---
 # GRO: Generic Receive Offload
 ---
 # Introduction
 ---
 ## Impact of fragmentation, segmentation on receive side
 큰 패킷이 N개의 패킷으로 단편화되면?
- 패킷 수신 시 인터럽트 N-번 발생
- 패킷 수신 시 라우팅 N번
- 패킷 수신 시 필터링 N번
- 등등
 단편화 횟수만큼 per-packet 오버헤드가 증가
 ---
 ## LRO: **Large** Receive Offload
 NIC/드라이버에서 **미리** 패킷을 결합해 커널로 전달하는 기술
 장점
- 커널의 패킷 처리(라우팅, 필터링, 파싱) 감소
- (NIC에서 결합 시) 인터럽트 감소
 단점
- NIC/드라이버가 헤더의 중요 정보를 삭제할 수도 있음
- NIC 벤더별로 동작이 다름
 ---
 ## GRO: **Generic** Receive Offload
 LRO의 일반화 버전
- 더 엄격한 결합 조건
- 다양한 프로토콜 지원
- 하드웨어 필수 요구사항 없음(HW 지원 시 결합 효율 높아짐)
- NAPI(New API) 위에서 동작
- 리눅스 2.6.29(2009년 3월)에 추가됨
 ---
 ## NAPI: New API
 softirq에서 폴링 기반으로 패킷을 수신하는 매커니즘
- mixed 매커니즘
  - 인터럽트: 첫 패킷
  - 폴링: 패킷 처리 중 수신되는 패킷들
 NIC queue 마다 NAPI 인스턴스가 생성됨(병렬 처리)
 ---
 ## NAPI: New API
 <style>
  .mermaid {
    max-height: 400px;
    overflow: auto;
  }
</style>
 <div class="mermaid">
sequenceDiagram
  participant nic as NIC
  box CPU
    participant kern as kernel
    participant dd as driver
  end
   rect rgb(235, 245, 255)
  Note over nic,dd: IRQ
  nic->>kern: interrupt
  kern->>dd: call halder
  dd->>kern: raise softirq
  end
   rect rgb(245, 235, 255)
  Note over kern,dd: NAPI
  kern->>dd: poll with budget
  dd->>dd: build skbs
  dd->>kern: pass skbs
  end
 </div>
 ---
 ## NAPI + GRO
 1. 드라이버의 NAPI poll 함수가 `napi_gro_receive` 함수로 패킷을 전달
2. `GRO table`의 `bucket`에 보관(`hold`)
3. 이후 전달되는 패킷과 `merge` 시도.
- bucket: GRO hash 테이블에서 RX flow hash 기반으로 선택된 구역(bucket)
- flush: 패킷을 GRO 계층에 보관하지 않고 처리
  - 보관된 패킷 flush
  - 새로 수신한 패킷 flush
 ---
 ## GRO table & bucket
 GRO table
- 8개의 bucket으로 구성
```c
u32 bucket = skb_get_hash_raw(skb) & (GRO_HASH_BUCKETS - 1);
```
 GRO bucket
- 최대 8개의 패킷을 보관
  - RX flow hash 지원 시 64(8 bucket x 8 packet)개의 패킷이 보관됨
```c
struct gro_list *gro_list = &gro->hash[bucket];
```
---
 # How GRO works
 ---
 ## gro_list
 선택된 bucket 내 패킷 리스트
- 새로 수신한 패킷(`skb`)과 결합할 패킷을 추리는데 사용됨
  - 상위 프로토콜로 전달되면서 결합 후보를 추림
    - ETH: MAC 헤더, VLAN이 다르면 제외 등
    - IPv4: 주소가 다르면 제외 등
    - TCP/UDP 포트가 다르면 제외 등
 ---
 ## GRO merge example: TCP merge
 다음의 경우 결합을 수행
- TCP source/destination port가 동일
- 새로 수신한 패킷에 CWR 플래그가 없는 경우
- TCP 옵션 헤더가 같은 경우 등
- 새로 수신한 패킷의 SEQ가 기존 수신 패킷의 바로 다음인 경우
  - SEQ가 바로 다음이 아닌 경우, 기존 패킷을 flush
 ---
 ## flush: protocol(previous packet: pp)
 `pp`: gro_list에 보관된 패킷 중 같은 플로우의 패킷
- TCP
  - 새로 수신한 패킷이 이전 패킷과 연속이 아닐 때
    - 패킷 드랍, 순서 뒤바뀜 등
  - 새로운 패킷의 플래그(CWR(Congestion Window Reduced), FIN(Finish), PSH(Push))
    - 긴급히 처리해야하는 패킷
 ---
 ## flush: protocol(new packet: skb)
 - IPv4: IP option header가 있는 경우, IP fragment된 경우 
- TCP
  - 새로 수신한 패킷이 이전 패킷과 연속이 아닐 때
    - 패킷 드랍, 순서 뒤바뀜 등
  - 새로운 패킷의 플래그(CWR(Congestion Window Reduced), FIN(Finish), PSH(Push))
    - 긴급히 처리해야하는 패킷
 ---
 ## flush: oldest
 GRO bucket이 가득 찰 경우 가장 오래된 패킷을 즉시 처리
 - bucket이 linked list이고, 새로운 패킷이 뒤로 추가되므로 가장 앞의 패킷을 처리
 ---
 ## flush: all
 `NAPI repoll`
- NAPI poll에는 실행 제한이 있음(패킷 개수, 시간))
- 실행 제한에 도달하면 NAPI poll을 멈추고 다시 스케쥴링 함
  - 바로 실행될 수도, 지연되어 실행될 수도 있음
- 더 처리할 패킷이 있는 경우 NAPI를 재실행하는 동작이 `repoll`임
 `napi_complete_done`
- 드라이버가 더 처리할 패킷이 없으면 이 함수를 호출해야 함
- 이 때 GRO table의 모든 패킷이 flush됨
 ---
 ## flush: timeout
 `gro_flush_timeout`: /sys/class/net/<INTERFACE>/gro_flush_timeout (default: 0)
`NAPI_GRO_CB(skb)->age`: 패킷이 GRO 계층에 전달된 시간을 기록(단위: jiffie)
 `gro_flush_timeout`이 설정되면 `age`를 참고하여 **최소 1 jiffie**는 GRO 계층에 보관함.
1. NAPI 종료 시(`napi_complete_done` 호출 시) 1 jiffie 미만의 skb는 flush하지 않음
2. 타이머를 실행, timeout 시간 후 NAPI가 repoll되어 flush 수행
만약 timeout 전에 NAPI가 실행되면 이 때 1 jiffie 이상의 패킷들이 flush됨
 ---