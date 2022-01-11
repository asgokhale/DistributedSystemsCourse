// we define a few macros here to avoid repetitive inclusion of 
// the ifdef ... else ... end if

#ifdef _WIN32 /* windows */
// windows type for process id
#define CS6381_PID          DWORD
// windows type for exit status
#define CS6381_STATUS        DWORD
// windows thread handle
#define CS6381_THR_HANDLE    HANDLE
// windows mutex handle
#define CS6381_MUTEX_HANDLE    HANDLE
// windows condition handle
#define CS6381_COND_HANDLE     HANDLE
// windows thread TSS key handle
#define CS6381_TSS_HANDLE      DWORD
// windows thread id
#define CS6381_THR_ID        DWORD
// windows socket handle
#define CS6381_SOCK_HANDLE SOCKET

// windows function to retrieve current process id
#define CS6381_GETPID()      GetCurrentProcessId ()
// windows function to exit
#define CS6381_EXIT(STATUS)  ExitProcess (STATUS)
// windows function to get current thread id
#define CS6381_GET_THR_ID()  GetCurrentThreadId ()
// windows return type for thread function
#define CS6381_THR_FUNC_RET_TYPE     DWORD WINAPI
// something gets screwed up due the DWORD WINAPI stuff when we define
// a function ptr typedef. Hence the need to distinguish
#define CS6381_THR_POOL_FUNC_RET_TYPE     DWORD
// windows param type for thread function
#define CS6381_THR_FUNC_PARAM_TYPE     LPVOID
// windows sleep func
#define CS6381_SLEEP(ARG)      Sleep (ARG*1000)
// windows usleep func
#define CS6381_USLEEP(ARG)      Sleep (ARG/1000)

#else /* Linux */

// unix type for process id
#define CS6381_PID           int
// unix type for exit status
#define CS6381_STATUS        int
// unix thread handle
#define CS6381_THR_HANDLE    pthread_t
// unix mutex handle
#define CS6381_MUTEX_HANDLE    pthread_mutex_t
// unix condition handle
#define CS6381_COND_HANDLE     pthread_cond_t
// unix thread TSS key handle
#define CS6381_TSS_HANDLE      pthread_key_t
// unix thread id
#define CS6381_THR_ID        pthread_t
// unix socket handle
#define CS6381_SOCK_HANDLE int


// unix function to retrieve process id
#define CS6381_GETPID()      getpid ()
// unix function to exit
#define CS6381_EXIT(STATUS)  exit (STATUS)
// unix function to get current thread id
#define CS6381_GET_THR_ID()  pthread_self ()
// unix return type for thread function
#define CS6381_THR_FUNC_RET_TYPE     void *
#define CS6381_THR_POOL_FUNC_RET_TYPE  CS6381_THR_FUNC_RET_TYPE
// unix param type for thread function
#define CS6381_THR_FUNC_PARAM_TYPE     void *
// unix sleep func
#define CS6381_SLEEP(ARG)      sleep (ARG)
// unix usleep func
#define CS6381_USLEEP(ARG)      usleep (ARG)

#endif /* if windows */


// complex typedef: declares a typedef to the thread function
// expected by the thread creation API
typedef CS6381_THR_POOL_FUNC_RET_TYPE (*CS6381_THR_FUNC) (CS6381_THR_FUNC_PARAM_TYPE);
