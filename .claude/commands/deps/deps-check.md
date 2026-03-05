# Dependency Check

Python 및 Node.js 의존성 상태를 점검합니다.

---

## 검사 항목

### 1. Python 의존성 점검

```bash
# requirements.txt와 실제 설치된 패키지 비교
pip list --format=columns 2>&1 | head -5

# requirements.txt의 패키지가 모두 설치되어 있는지 확인
python -c "
import pkg_resources
import sys

with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

missing = []
outdated = []
ok = []

for req in requirements:
    pkg_name = req.split('>=')[0].split('==')[0].split('<')[0].strip()
    try:
        dist = pkg_resources.get_distribution(pkg_name)
        ok.append(f'{pkg_name} ({dist.version})')
    except pkg_resources.DistributionNotFound:
        missing.append(pkg_name)

print(f'설치됨: {len(ok)}개')
for p in ok:
    print(f'  OK: {p}')

if missing:
    print(f'\n미설치: {len(missing)}개')
    for p in missing:
        print(f'  MISSING: {p}')
    print(f'\n설치 명령: pip install {\" \".join(missing)}')
else:
    print('\n모든 Python 의존성이 설치되어 있습니다.')
"
```

### 2. Node.js 의존성 점검

```bash
cd frontend

# node_modules 존재 여부
ls node_modules/.package-lock.json 2>/dev/null && echo "node_modules: OK" || echo "node_modules: MISSING (npm install 필요)"

# 보안 취약점 점검
npm audit --production 2>&1 | tail -5

# 구버전 패키지 확인
npm outdated 2>&1 | head -15
```

### 3. Python 실행 환경 확인

```bash
python --version
which python
pip --version
```

### 4. Node.js 실행 환경 확인

```bash
node --version
npm --version
```

---

## 출력 형식

```
[의존성 점검 결과]

1. Python 환경
   - Python: 3.12.x
   - 패키지: N/N 설치됨
   - 미설치: [목록]

2. Node.js 환경
   - Node: v20.x.x
   - npm: 10.x.x
   - node_modules: OK/MISSING
   - 보안 취약점: N건

3. 조치 필요 사항
   - pip install [미설치 패키지]
   - npm install (필요시)
```

---

## 주의사항

- 읽기 전용 검사입니다 (패키지 설치/삭제하지 않음)
- 조치가 필요한 경우 명령어를 안내합니다
