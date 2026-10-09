# 건설기계 마켓 레이더 — 자체 호스팅 버전

이 폴더를 그대로 웹서버(GitHub Pages, 사내 웹서버 등)에 올리면 브라우저만으로 열립니다. 로그인이 필요 없습니다.

## GitHub Pages에 올리기 (약 5분)
1. github.com 로그인 → New repository → 이름 `market-radar` (Public) → Create repository.
2. 저장소 페이지의 "uploading an existing file" 링크 → 이 폴더의 index.html, README.md, .nojekyll 과 data 폴더(json 4개)를 드래그해 업로드 → Commit changes.
3. Settings → Pages → Build and deployment: Source "Deploy from a branch", Branch "main" / "(root)" → Save.
4. 1~2분 뒤 https://<GitHub아이디>.github.io/market-radar/ 로 접속됩니다. 이 주소를 공유하세요.

## 방문자 통계 (GoatCounter, 무료·광고 없음)
1. https://www.goatcounter.com/signup 에서 가입. Code 칸에 `soosan-radar` 입력. 이미 사용 중인 코드라면 다른 이름을 쓰고 index.html 안의 `soosan-radar` 두 곳을 같은 이름으로 바꾸세요.
2. 가입 후 https://soosan-radar.goatcounter.com 에서 방문자 수(고유 방문자), 페이지뷰, 탭별 조회(이벤트 /tab/overview 등), 유입 경로, 국가, 기기를 볼 수 있습니다. Settings → "Public"을 켜면 통계 페이지 자체도 링크로 공유됩니다.
3. 가입 전에는 카운터 스크립트가 조용히 무시되므로 페이지는 정상 동작합니다.

## 월간 갱신
매월 10일 예약 작업이 새 데이터 파일(data/market.json, macro.json, imf.json, vn_trailer.json)을 만들어 대화로 전달합니다. GitHub 저장소의 data 폴더에 같은 이름으로 업로드(덮어쓰기)하면 반영됩니다. 저장소를 PC에 클론한 폴더를 Claude 데스크톱 앱에 연결해 두면 이 단계도 자동으로 커밋·푸시하도록 바꿀 수 있습니다.

## 참고
자체 호스팅 버전에는 claude.ai 저장소를 쓰는 등록 기능(제품·기업·관심 국가 추가)이 빠져 있습니다. 등록은 claude.ai 대시보드에서 하고, 월간 갱신 때 반영됩니다.
