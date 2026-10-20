import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

POLICY_ID = '20261019-ppl-tolerance-5pct'
LOWER, UPPER, BASELINE = 2.63112, 2.90808, 2.7696


def reassess(record, reference):
    if not record:
        return {'verdict':'未运行', 'reason':'没有完整PPL JSON，不补造指标'}
    reason = None
    if record.get('schema') != 'llama_cpp_ppl_regression_v1':
        reason = '原始记录schema不匹配'
    elif record.get('status') not in ['PASS', 'FAIL']:
        reason = '没有原评测器完成后的数值判定'
    elif record.get('conditions') != reference['conditions']:
        reason = '模型分片、数据哈希或固定参数不匹配'
    elif record.get('baseline_ppl') != BASELINE:
        reason = '参考PPL不匹配'
    elif not isinstance(record.get('elapsed_seconds'), (int,float)) or not 0 <= record['elapsed_seconds'] <= 590:
        reason = '未证实原始运行符合590秒时限'
    value = record.get('ppl')
    if not isinstance(value, (int,float)) or not math.isfinite(value) or value <= 0:
        reason = 'PPL不是有限正数'
    if reason:
        return {'verdict':'无法确认', 'reason':reason}
    return {'verdict':'PASS' if LOWER <= value <= UPPER else 'FAIL',
            'reason':'按既有完整JSON复核；未重跑；原运行状态与容差不改写',
            'relative_difference_percent':100*(value/BASELINE-1),
            'conditions_match':True}


def add_policy_review(book, jobs, evidence):
    reference_path = evidence/'ppl_policy_reference.json'
    reference = json.loads(reference_path.read_text(encoding='utf-8'))
    assert reference['ppl'] == BASELINE
    sheet = book.create_sheet('PPL新规复核')
    sheet.append(['作业ID','版本','PPL','原运行PPL状态','原容差(%)','现行5%状态',
                  '模型/数据/条件一致','参考PPL','含边界下限','含边界上限',
                  '相对差异(%)','是否重跑','源JSON','复核说明'])
    reviews = []
    lookup = {}
    job_reviews = {}
    for job in jobs:
        for measurement in job['measurements']:
            record = measurement.get('ppl')
            if not record:
                sheet.append([job['job_id'],measurement['name'],None,'未运行',None,
                              '未运行','待校验',BASELINE,LOWER,UPPER,None,'未重跑',
                              measurement['path']+'/perplexity_result.json',
                              '尚无完整PPL JSON，不得据其他版本的PASS替代'])
                continue
            result = reassess(record, reference)
            source = measurement.get('ppl_gate_path',measurement['path']+'/perplexity_result.json')
            item = dict(result, job_id=job['job_id'], name=measurement['name'],
                        ppl=record.get('ppl'), original_status=record.get('status'),
                        original_tolerance_percent=record.get('tolerance_percent'),
                        source_result_path=source, rerun=False,
                        parsed_record_sha256=hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest())
            lookup[(job['job_id'],measurement['name'])] = item
            job_reviews.setdefault(job['job_id'],[]).append(item)
            reviews.append(item)
            sheet.append([job['job_id'],measurement['name'],record.get('ppl'),
                          record.get('status'),record.get('tolerance_percent'),result['verdict'],
                          '一致' if result.get('conditions_match') else result['reason'],
                          BASELINE,LOWER,UPPER,result.get('relative_difference_percent'),
                          '未重跑',source,result['reason']])
    log = book['作业日志']
    jobs_by_id = {item['job_id']:item for item in jobs}
    log.cell(1,25,'现行5% PPL状态')
    log.cell(1,26,'新规复核口径')
    for row in range(2,log.max_row+1):
        jid = str(log.cell(row,1).value)
        current_job = jobs_by_id[jid]
        cases = job_reviews.get(jid,[])
        if not cases:
            log.cell(row,25,'无完整PPL')
            continue
        if 'PGO' in str(log.cell(row,8).value) and len(cases)==1 and cases[0]['name'].startswith('compiler-control_'):
            current = '仅control '+cases[0]['verdict']+'；PGO'+('待校验' if current_job['state'] in ['RUN','PEND'] else '未校验')
        elif len(cases)<len(current_job['measurements']):
            current = '多版本尚未全部校验（见明细）'
        else:
            current = cases[0]['verdict'] if len(cases)==1 else '多版本见新规复核页'
        log.cell(row,25,current)
        log.cell(row,26,'现行±5%；既有完整JSON复核，非重跑；原PPL状态及LSF状态保留')
        newly_passed = [item for item in cases if item['original_status']=='FAIL' and item['verdict']=='PASS']
        if newly_passed:
            log.cell(row,5,str(log.cell(row,5).value)+'\n新规则复核：'+
                     '；'.join(item['name']+' PPL='+str(item['ppl'])+'，±5% PASS（原±0.5% FAIL）' for item in newly_passed)+
                     '。原作业未完成的测速仍未运行，不补算分数。')
    detail = book['运行结果']
    first_column = detail.max_column+1
    detail.cell(1,first_column,'现行5% PPL状态')
    detail.cell(1,first_column+1,'原运行容差(%)')
    for row in range(2,detail.max_row+1):
        item = lookup.get((str(detail.cell(row,1).value),str(detail.cell(row,2).value)))
        if item:
            detail.cell(row,first_column,item['verdict'])
            detail.cell(row,first_column+1,item['original_tolerance_percent'])
    data = {'policy_id':POLICY_ID, 'reviewed_at_hkt':datetime.now(timezone(timedelta(hours=8))).isoformat(),
            'baseline_ppl':BASELINE,'tolerance_percent':5.0,'accepted_interval_inclusive':[LOWER,UPPER],
            'reference_path':str(reference_path),'reference_sha256':hashlib.sha256(reference_path.read_bytes()).hexdigest(),
            'scope':'Existing completed PPL JSON only; no inference rerun; original results and LSF states preserved; no missing performance imputed',
            'reviews':reviews}
    path = evidence/'ppl_policy5_reassessment.json'
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    book['说明'].append(['PPL规则更新','用户通知：±0.5%改为±5%，含边界[2.63112,2.90808]；其余条件不变。原状态保留，现行判定见新增列及PPL新规复核页。'])
    book['LSF与配置证据'].append(['无（规则变更）',str(path),json.dumps({k:v for k,v in data.items() if k!='reviews'},ensure_ascii=False)])
    for item in reviews:
        if item['original_status']=='FAIL':
            book['LSF与配置证据'].append([item['job_id'],str(path),json.dumps(item,ensure_ascii=False)])
