"""自定义异常类"""


class S1CLIException(Exception):
    """S1CLI 基础异常"""
    pass


class NetworkError(S1CLIException):
    """网络错误"""
    pass


class AuthenticationError(S1CLIException):
    """认证错误"""
    pass


class ParseError(S1CLIException):
    """解析错误"""
    pass


class APIError(S1CLIException):
    """API 错误"""
    pass


class SessionExpiredError(AuthenticationError):
    """会话过期"""
    pass


class RateLimitError(S1CLIException):
    """请求频率限制"""
    pass

