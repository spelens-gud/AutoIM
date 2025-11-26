# Go 测试文件编写规范

本规范定义了为 Go 组件编写测试文件的标准格式和内容要求。

## 测试文件类型

### 1. 单元测试文件（*_test.go）

- 文件名：`功能名_test.go`（如 `config_test.go`）
- 包名：与被测试包相同或添加 `_test` 后缀
- 用途：测试单个函数、方法或类型的行为

### 2. 基准测试文件（benchmark_test.go）

- 文件名：`benchmark_test.go`
- 包名：与被测试包相同
- 用途：性能测试和性能回归检测

### 3. 示例测试文件（example_test.go）

- 文件名：`example_test.go`
- 包名：被测试包名 + `_test` 后缀
- 用途：提供可执行的文档示例

## 单元测试规范

### 测试函数命名

```go
// 格式：Test + 被测试函数名 + [_特定场景]
func TestGetEnv(t *testing.T) { }
func TestGetEnv_EmptyValue(t *testing.T) { }
func TestEnv_IsDevelopment(t *testing.T) { }
```

**命名规则：**
- 以 `Test` 开头
- 使用驼峰命名法
- 方法测试使用 `Test + 类型名 + _ + 方法名`
- 特定场景测试添加下划线和场景描述

### 测试结构 - 表驱动测试

推荐使用表驱动测试模式：

```go
func TestFunctionName(t *testing.T) {
	tests := []struct {
		name    string    // 测试用例名称（中文）
		input   InputType // 输入参数
		want    WantType  // 期望输出
		wantErr bool      // 是否期望错误
	}{
		{
			name:    "正常情况",
			input:   validInput,
			want:    expectedOutput,
			wantErr: false,
		},
		{
			name:    "边界情况",
			input:   boundaryInput,
			want:    boundaryOutput,
			wantErr: false,
		},
		{
			name:    "错误情况",
			input:   invalidInput,
			want:    zeroValue,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := FunctionName(tt.input)
			
			if (err != nil) != tt.wantErr {
				t.Errorf("FunctionName() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			
			if !tt.wantErr && got != tt.want {
				t.Errorf("FunctionName() = %v, want %v", got, tt.want)
			}
		})
	}
}
```

**要点：**
- 测试用例名称使用中文，清晰描述测试场景
- 使用 `t.Run()` 创建子测试
- 先检查错误，再检查返回值
- 错误信息包含实际值和期望值

### 测试覆盖场景

每个函数/方法至少测试以下场景：

1. **正常情况** - 典型的有效输入
2. **边界情况** - 空值、零值、最大值、最小值
3. **错误情况** - 无效输入、异常条件
4. **特殊情况** - 业务逻辑的特殊分支

### 测试辅助函数

```go
// 测试前的准备工作
func setupTest(t *testing.T) (*TestContext, func()) {
	// 初始化测试环境
	ctx := &TestContext{}
	
	// 返回清理函数
	cleanup := func() {
		// 清理资源
	}
	
	return ctx, cleanup
}

// 使用示例
func TestWithSetup(t *testing.T) {
	ctx, cleanup := setupTest(t)
	defer cleanup()
	
	// 测试代码
}
```

### 并发测试

```go
func TestConcurrent(t *testing.T) {
	const goroutines = 100
	const iterations = 100

	var wg sync.WaitGroup
	wg.Add(goroutines)

	for i := 0; i < goroutines; i++ {
		go func(id int) {
			defer wg.Done()
			for j := 0; j < iterations; j++ {
				// 并发操作
			}
		}(i)
	}

	wg.Wait()
	
	// 验证结果
}
```

### Mock 和 Stub

```go
// Mock 接口实现
type mockInterface struct {
	callCount int
	returnVal interface{}
	returnErr error
}

func (m *mockInterface) Method(param Type) (Type, error) {
	m.callCount++
	return m.returnVal.(Type), m.returnErr
}

// 使用 Mock
func TestWithMock(t *testing.T) {
	mock := &mockInterface{
		returnVal: expectedValue,
		returnErr: nil,
	}
	
	// 测试代码
	
	if mock.callCount != 1 {
		t.Errorf("期望调用1次，实际调用%d次", mock.callCount)
	}
}
```

## 基准测试规范

### 基准测试命名

```go
// 格式：Benchmark + 被测试函数名 + [_场景]
func BenchmarkGetEnv(b *testing.B) { }
func BenchmarkConfigType_Unmarshal_JSON(b *testing.B) { }
func BenchmarkConcurrent(b *testing.B) { }
```

### 基准测试结构

```go
func BenchmarkFunctionName(b *testing.B) {
	// 准备测试数据（不计入性能测试）
	testData := prepareData()
	
	// 重置计时器
	b.ResetTimer()
	
	// 性能测试循环
	for i := 0; i < b.N; i++ {
		FunctionName(testData)
	}
}
```

### 内存分配测试

```go
func BenchmarkWithMemory(b *testing.B) {
	b.ReportAllocs() // 报告内存分配
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// 测试代码
	}
}
```

### 并行基准测试

```go
func BenchmarkParallel(b *testing.B) {
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			// 并行执行的代码
		}
	})
}
```

### 基准测试分组

```go
func BenchmarkOperations(b *testing.B) {
	b.Run("Small", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			// 小数据量测试
		}
	})
	
	b.Run("Large", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			// 大数据量测试
		}
	})
}
```

## 示例测试规范

### 示例函数命名

```go
// 包级示例
func Example() { }

// 函数示例
func ExampleFunctionName() { }

// 方法示例
func ExampleType_MethodName() { }

// 带后缀的示例（同一函数多个示例）
func ExampleFunctionName_scenario() { }
```

### 示例测试结构

```go
func Example_basicUsage() {
	// 示例代码
	result := FunctionName("input")
	fmt.Println(result)
	
	// Output:
	// expected output
}

func ExampleType_Method() {
	obj := NewType()
	result := obj.Method()
	fmt.Printf("结果: %v\n", result)
	
	// Output:
	// 结果: expected
}
```

**要点：**
- 示例必须可执行
- 使用 `// Output:` 注释验证输出
- 输出必须精确匹配（包括空格）
- 示例名称使用中文或英文描述场景

## 测试文件组织

### 文件结构

```
package_name/
├── file.go              # 源代码
├── file_test.go         # 单元测试
├── another_test.go      # 其他单元测试
├── benchmark_test.go    # 基准测试
└── example_test.go      # 示例测试
```

### 测试分组原则

1. **按功能模块分文件** - 每个源文件对应一个测试文件
2. **基准测试独立** - 所有基准测试放在 `benchmark_test.go`
3. **示例测试独立** - 所有示例放在 `example_test.go`

## 测试注释规范

### 测试函数注释

```go
// TestFunctionName 测试函数功能的简短描述
func TestFunctionName(t *testing.T) {
	// 测试代码
}

// BenchmarkFunctionName 基准测试函数性能
func BenchmarkFunctionName(b *testing.B) {
	// 基准测试代码
}
```

### 测试用例注释

```go
tests := []struct {
	name string // 测试用例名称
	// 其他字段
}{
	{
		name: "正常情况 - 有效输入返回正确结果",
		// ...
	},
	{
		name: "边界情况 - 空字符串返回默认值",
		// ...
	},
}
```

## 测试断言

### 基本断言

```go
// 相等性检查
if got != want {
	t.Errorf("FunctionName() = %v, want %v", got, want)
}

// 错误检查
if err != nil {
	t.Errorf("FunctionName() 返回错误: %v", err)
}

// 布尔检查
if !condition {
	t.Error("期望条件为真，实际为假")
}
```

### 深度比较

```go
import "reflect"

if !reflect.DeepEqual(got, want) {
	t.Errorf("FunctionName() = %+v, want %+v", got, want)
}
```

### 字符串包含检查

```go
import "strings"

if !strings.Contains(got, expected) {
	t.Errorf("期望包含 %q，实际为 %q", expected, got)
}
```

## 测试覆盖率要求

### 目标覆盖率

- **核心功能包**: ≥ 90%
- **工具包**: ≥ 85%
- **接口包**: ≥ 80%

### 覆盖率检查

```bash
# 生成覆盖率报告
go test -cover ./...

# 详细覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out

# HTML 覆盖率报告
go tool cover -html=coverage.out
```

## 测试最佳实践

### 1. 测试独立性

- 每个测试应该独立运行
- 不依赖测试执行顺序
- 清理测试产生的副作用

```go
func TestIndependent(t *testing.T) {
	// 准备
	setup()
	defer cleanup()
	
	// 测试
	// ...
}
```

### 2. 测试可读性

- 使用清晰的变量名
- 测试用例名称描述性强
- 适当添加注释说明复杂逻辑

### 3. 测试可维护性

- 避免重复代码，提取辅助函数
- 使用表驱动测试减少冗余
- 保持测试代码简洁

### 4. 测试完整性

- 覆盖正常路径和异常路径
- 测试边界条件
- 测试并发安全性（如适用）

### 5. 性能考虑

- 避免在测试中进行耗时操作
- 使用 Mock 替代外部依赖
- 基准测试使用真实数据规模

## 常见测试模式

### 1. 表驱动测试

适用于：多个输入输出组合的测试

```go
func TestTableDriven(t *testing.T) {
	tests := []struct {
		name string
		// 字段
	}{
		// 测试用例
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// 测试逻辑
		})
	}
}
```

### 2. 子测试

适用于：相关测试的分组

```go
func TestSubtests(t *testing.T) {
	t.Run("场景1", func(t *testing.T) {
		// 测试代码
	})
	
	t.Run("场景2", func(t *testing.T) {
		// 测试代码
	})
}
```

### 3. 测试夹具

适用于：需要共享设置和清理的测试

```go
func TestMain(m *testing.M) {
	// 全局设置
	setup()
	
	// 运行测试
	code := m.Run()
	
	// 全局清理
	cleanup()
	
	os.Exit(code)
}
```

### 4. 黑盒测试

适用于：测试公共 API

```go
package mypackage_test

import (
	"testing"
	"mypackage"
)

func TestPublicAPI(t *testing.T) {
	// 只能访问导出的符号
}
```

## 测试文档化

### 测试说明注释

```go
// TestComplexScenario 测试复杂场景
//
// 此测试验证以下行为：
// 1. 初始化时正确加载配置
// 2. 配置变更时触发回调
// 3. 错误情况下返回默认值
func TestComplexScenario(t *testing.T) {
	// 测试代码
}
```

### 测试用例文档

对于复杂的测试逻辑，添加注释说明：

```go
tests := []struct {
	name string
	// ...
}{
	{
		// 测试场景：当配置文件不存在时，应该返回默认配置
		// 预期行为：不返回错误，使用内置默认值
		name: "配置文件不存在使用默认值",
		// ...
	},
}
```

## 质量检查清单

完成测试文件后，检查以下项目：

- [ ] 所有公共函数都有测试
- [ ] 测试覆盖率达到要求
- [ ] 测试用例名称清晰（使用中文）
- [ ] 包含正常、边界、错误场景
- [ ] 测试可以独立运行
- [ ] 基准测试使用 `b.ResetTimer()`
- [ ] 示例测试有 `// Output:` 注释
- [ ] 并发测试使用 `sync.WaitGroup`
- [ ] 测试代码遵循 Go 代码规范
- [ ] 无测试警告和错误
- [ ] 测试执行速度合理
- [ ] Mock 对象行为正确

## 运行测试命令

```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./package/path

# 运行特定测试
go test -run TestFunctionName

# 详细输出
go test -v ./...

# 覆盖率测试
go test -cover ./...

# 基准测试
go test -bench=. ./...

# 基准测试（指定时间）
go test -bench=. -benchtime=5s ./...

# 基准测试（内存分配）
go test -bench=. -benchmem ./...

# 竞态检测
go test -race ./...
```
