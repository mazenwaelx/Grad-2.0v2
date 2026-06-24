using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace LawyerConnect.Migrations
{
    /// <inheritdoc />
    public partial class AlterTableRefreshTokenMigration : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "RevokeReason",
                table: "RefreshTokens",
                type: "nvarchar(max)",
                nullable: true);

            migrationBuilder.AddColumn<DateTime>(
                name: "RevokedDate",
                table: "RefreshTokens",
                type: "datetime2",
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "RevokeReason",
                table: "RefreshTokens");

            migrationBuilder.DropColumn(
                name: "RevokedDate",
                table: "RefreshTokens");
        }
    }
}
