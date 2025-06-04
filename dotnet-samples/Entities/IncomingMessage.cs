namespace cw_repeated_calls_dotnet.Entities
{
    internal record IncomingMessage
    {
        public int CustomerId { get; set; }
        public string Message { get; set; }
        public DateTime TimeStamp { get; set; }
    }
}