namespace LawyerConnect.DTOs
{
    public class AIChatRequestDto
    {
        public string Message { get; set; } = string.Empty;
        public string ChatId { get; set; } = string.Empty;
    }

    public class AIChatResponseDto
    {
        public string Response { get; set; } = string.Empty;
        public string ChatId { get; set; } = string.Empty;
        public bool FilesRemoved { get; set; }
        public List<string> RemovedFiles { get; set; } = new();
    }

    public class AIChatHistoryDto
    {
        public string ChatId { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
    }

    public class AIChatMessageDto
    {
        public int Id { get; set; }
        public string Text { get; set; } = string.Empty;
        public string Sender { get; set; } = string.Empty; // "user" or "ai"
        public DateTime Timestamp { get; set; }
    }

    public class FileUploadResponseDto
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public string? FileHash { get; set; }
        public int? DocumentCount { get; set; }
    }

    public class UploadedFileDto
    {
        public string Hash { get; set; } = string.Empty;
        public string Filename { get; set; } = string.Empty;
        public DateTime UploadedAt { get; set; }
        public int DocumentCount { get; set; }
    }
}
