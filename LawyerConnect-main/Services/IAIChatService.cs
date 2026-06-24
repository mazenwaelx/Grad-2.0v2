using LawyerConnect.DTOs;

namespace LawyerConnect.Services
{
    public interface IAIChatService
    {
        Task<AIChatResponseDto> SendMessageAsync(string message, string userId, string chatId);
        Task<List<AIChatHistoryDto>> GetUserChatsAsync(string userId);
        Task<List<AIChatMessageDto>> GetChatMessagesAsync(string chatId, string userId);
        Task DeleteChatAsync(string chatId, string userId);
        Task<FileUploadResponseDto> UploadFileAsync(IFormFile file);
        Task<List<UploadedFileDto>> GetUploadedFilesAsync();
        Task DeleteFileAsync(string fileHash);
        Task<bool> CheckHealthAsync();
    }
}
