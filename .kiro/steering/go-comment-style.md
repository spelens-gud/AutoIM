# Go 代码注释规范

## 注释格式规则

本项目遵循以下 Go 代码注释规范

### 1. 常量注释

常量注释格式：`// 常量名 描述`

```go
const (
    // ConfigTypeUnknown 配置文件类型未知
    ConfigTypeUnknown ConfigType = iota
    // ConfigTypeJson 配置文件类型JSON
    ConfigTypeJson
    // ConfigTypeYaml 配置文件类型YAML
    ConfigTypeYaml
)
```

### 2. 类型定义注释

类型注释格式：`// 类型名 类型种类 描述.`

- interface: `// InterfaceName interface 描述.`
- struct: `// StructName struct 描述.`
- type alias: `// TypeName 描述.`

```go
// ConfigLoader interface 配置加载器.
ConfigLoader interface {
    // LoadContext 加载配置文件
    LoadContext(ctx context.Context, configRoot interface{}) (err error)
}

// Env 环境
Env string

// ConfigType 配置文件类型
ConfigType uint
```

### 3. 接口方法注释

接口方法注释格式：`// 方法名 描述`

```go
type ConfigLoader interface {
    // LoadContext 加载配置文件
    LoadContext(ctx context.Context, configRoot interface{}) (err error)
    // Load 加载配置文件
    Load(configRoot interface{}) (err error)
    // MustLoad 加载配置文件
    MustLoad(configRoot interface{})
}
```

### 4. 函数注释

函数注释格式：`// 函数名 function 描述.`

```go
// GetEnv function 获取环境变量.
func GetEnv() Env { return Env(env.Get()) }

// SetEnv function 设置环境变量.
func SetEnv(e string) {
    fmt.Printf("[SYCORE] env updated [ %s ]\n", e)
    env.Set(e)
}
```

### 5. 方法注释

方法注释格式：`// 方法名 method 描述.`

```go
// String method 获取环境变量字符串.
func (env Env) String() string {
    // ...
}

// IsDevelopment method 配置文件是否是开发环境.
func (env Env) IsDevelopment() bool { 
    return env == Development || len(env) == 0 
}
```

### 6. 变量注释

变量注释格式：`// 变量名 类型 描述.`

```go
// env var 获取环境变量.
var env = configString{
    Init: func() string {
        // ...
    },
}
```

### 7. 结构体字段注释

结构体字段可以使用行内注释或独立注释：

```go
// env struct 获取环境变量.
type Config struct {
    // Host 主机地址
    Host string `json:"host"`
    // Port 端口号
    Port int `json:"port"`
}
```

## 注释原则

1. **必须使用中文**：所有注释必须使用中文描述
2. **格式统一**：严格遵循 `名称 + 类型标识 + 描述` 的格式
3. **简洁明了**：描述应简洁准确，避免冗余
4. **类型标识**：
   - `interface` - 接口类型
   - `struct` - 结构体类型
   - `function` - 包级函数
   - `method` - 类型方法
   - `type` - 类型别名（可省略）
5. **导出符号必须注释**：所有导出的类型、函数、方法、常量、变量都必须有注释
6. **接口方法注释**：接口内的方法注释只需 `方法名 + 描述`，不需要 `method` 标识
7. **必须使用.结尾**：所有注释必须使用.结尾

## 适用范围

- 其他目录可参考此规范，但可根据实际情况调整
