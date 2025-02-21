# 文件结构

```bash
services/
├── auth/                    # 认证与授权
│   ├── auth_service.py
│   ├── rbac_service.py
│   └── user_service.py
│
├── academic/               # 教务管理
│   ├── teaching/
│   │   ├── course_service.py
│   │   ├── class_service.py
│   │   └── teaching_service.py
│   │
│   ├── student/
│   │   ├── student_service.py
│   │   ├── grade_service.py
│   │   └── attendance_service.py
│   │
│   └── organization/
│       ├── department_service.py
│       └── major_service.py
│
├── enrollment/             # 招生管理
│   └── enrollment_service.py
│
├── activity/              # 活动管理
│   └── activity_service.py
│
└── evaluation/            # 评教系统
    └── evaluation_service.py
```

# 模块说明

## 认证服务 (auth/)

认证服务模块，包含用户认证、授权和权限管理相关功能。

### 功能列表

- 用户认证 (auth_service.py)
- 用户管理 (user_service.py)
- 权限管理 (rbac_service.py)

### 主要接口

#### 用户认证

- 登录
- 注册
- 密码重置
- Token管理

#### 用户管理

- 用户CRUD
- 用户信息更新
- 用户状态管理

#### 权限管理

- 角色管理
- 权限分配
- 权限验证

## 教务管理 (academic/)

学术服务总模块，包含教学、学生和组织管理相关功能。

### 子模块

#### 教学服务 (teaching/)

- 教师管理
- 课程管理
- 班级管理
- 教学计划

##### 教师管理 (teacher_service.py)

- 教师信息CRUD
- 教师资质管理
- 教师工作量统计

##### 教学管理 (teaching_service.py)

- 教学任务分配
- 教学进度管理
- 教学质量监控

##### 课程管理 (course_service.py)

- 课程信息CRUD
- 课程安排
- 课程资源管理

##### 班级管理 (class_service.py)

- 班级信息CRUD
- 班级课表管理
- 班级学生管理

#### 学生服务 (student/)

- 学生信息管理
- 成绩管理
- 考勤管理
- 学籍管理

##### 学生管理 (student_service.py)

- 学生信息CRUD
- 学籍管理
- 学生档案管理

##### 学生服务管理 (student_management_service.py)

- 学生选课
- 学生请假
- 学生奖惩
- 学生活动参与

##### 成绩管理 (grade_service.py)

- 成绩录入
- 成绩统计
- 成绩分析
- GPA计算

##### 考勤管理 (attendance_service.py)

- 考勤记录
- 考勤统计
- 请假管理
- 出勤率分析

#### 组织服务 (organization/)

- 院系管理
- 专业管理
- 班级组织

##### 院系管理 (department_service.py)

- 院系信息CRUD
- 院系结构管理
- 院系统计分析
- 院系人员管理

##### 专业管理 (major_service.py)

- 专业信息CRUD
- 专业课程计划
- 专业招生计划
- 专业发展规划

### 模块间关系

- 教学服务依赖组织服务提供的院系和专业信息
- 学生服务依赖教学服务提供的课程和班级信息
- 组织服务为其他服务提供基础数据支持

## 招生管理 (enrollment/)

招生服务模块，包含招生计划、报名和录取相关功能。

### 功能列表 (enrollment_service.py)

#### 招生计划管理

- 计划制定
- 计划审核
- 计划发布
- 计划调整

#### 报名管理

- 考生信息管理
- 报名信息验证
- 考试安排
- 考场管理

#### 录取管理

- 成绩导入
- 录取规则配置
- 录取过程管理
- 录取结果发布

#### 统计分析

- 报名情况统计
- 录取情况分析
- 生源地分析
- 专业志愿分析

### 接口依赖

- 依赖组织服务提供专业信息
- 与学生服务交互进行新生信息转换
- 与教学服务交互进行班级分配

## 活动管理 (activity/)

活动服务模块，包含学生活动和社团管理相关功能。

### 功能列表 (activity_service.py)

#### 活动管理

- 活动信息CRUD
- 活动审批流程
- 活动场地管理
- 活动经费管理

#### 社团管理

- 社团信息CRUD
- 社团成员管理
- 社团活动管理
- 社团考核管理

#### 活动参与

- 活动报名
- 签到管理
- 活动反馈
- 活动评价

#### 统计分析

- 活动参与度分析
- 社团活跃度分析
- 学生参与情况统计
- 活动效果评估

### 接口依赖

- 与学生服务交互获取学生信息
- 与组织服务交互进行场地管理
- 与评教服务交互进行活动评价

## 评教系统 (evaluation/)

评教服务模块，包含教学评价和质量监控相关功能。

### 功能列表 (evaluation_service.py)

#### 评教管理

- 评教计划制定
- 评教指标管理
- 评教过程管理
- 评教结果管理

#### 质量监控

- 教学质量评估
- 课程质量监控
- 教师教学监控
- 学生学习监控

#### 反馈管理

- 学生评教
- 同行评教
- 督导评教
- 自我评教

#### 统计分析

- 评教数据分析
- 质量趋势分析
- 问题诊断分析
- 改进建议生成

### 接口依赖

- 与教学服务交互获取课程和教师信息
- 与学生服务交互获取学生信息
- 与组织服务交互获取院系信息

# 功能优化 