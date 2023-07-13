# Zen UV Core API
The general objective of the core is to calculate mapping and isomorphism of two structures without geometry usage

|Language|Polys|Tris|Verts|Elapsed Time|
|---|---|---|---|---|
|C++|148745|251085|148651|~9000ms|
|Python|148745|251085|148651|~68000ms|

## Zen UV Fast Calculation Utils
Creates an instance of ZenUv calculating object
```cpp
extern "C" ZEN_UV_API ZenUv* ZenUv_new();
```

Deletes an instance of ZenUv calculating object
```cpp
extern "C" ZEN_UV_API void ZenUv_delete(ZenUv* val);
```

Prepare structure data for calcution
```cpp
extern "C" ZEN_UV_API void ZenUv_appendAdj(ZenUv* val, 
            int32_t type,
            int32_t key,
            int32_t *input,
            uint32_t size);
```

Calculates mapping and isomorphism of two structures without geometry usage
```cpp
extern "C" ZEN_UV_API int32_t* ZenUv_calc(ZenUv* val,
            bool &similar, int32_t &outSize, int32_t &errorCode);
```

Retrieves the last calculating error
```cpp
extern "C" ZEN_UV_API const char *ZenUv_getErrorStr(int32_t errorCode);
```

## Zen UV OS Utils
We tried to perform the fastest calculation algorithm for mapping and isomorphism of two structures without geometry usage but still some procedures may take a long time period that's why we use OS utils to inform users about progress of operation

Creates OS Object
```cpp
extern "C" ZEN_UV_API ZenUvOS* ZenUvOS_new();
```

Deletes OS Object
```cpp
extern "C" ZEN_UV_API void ZenUvOS_delete(ZenUvOS* val);
```

### ProgressBar Utils
![image](https://user-images.githubusercontent.com/18611095/123287424-64f9f900-d517-11eb-9b29-724ed79d101c.png)

![image](https://user-images.githubusercontent.com/18611095/123287653-8eb32000-d517-11eb-97e1-5cc795511899.png)

Prepare progress theme by setting colors
```cpp
extern "C" ZEN_UV_API void ZenUvOS_SetTaskbarProgressTheme(ZenUvOS* val,
            ZenUvProgressTheme theme);
```

Setup progress bounds
```cpp
extern "C" ZEN_UV_API void ZenUvOS_SetTaskbarProgressBounds(ZenUvOS* val,
            ZenUvProgressBounds bounds);
```

Sets current progress value
```cpp
extern "C" ZEN_UV_API void ZenUvOS_SetTaskbarProgress(ZenUvOS* val,
            uint64_t position, uint64_t max, const wchar_t *text);
```

Show or hide progress
```cpp
extern "C" ZEN_UV_API void ZenUvOS_SetTaskbarProgressVisible(ZenUvOS* val,
            bool visible, const wchar_t *text);
```

Gets main window title
```cpp
extern "C" ZEN_UV_API void ZenUvOS_GetMainWindowTitle(ZenUvOS* val,
            wchar_t *text, uint32_t size);
```

Sets main window title
```cpp
extern "C" ZEN_UV_API void ZenUvOS_SetMainWindowTitle(ZenUvOS* val,
            const wchar_t *text);
```
