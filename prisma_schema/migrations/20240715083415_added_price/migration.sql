/*
  Warnings:

  - Added the required column `price` to the `FormData` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "FormData" ADD COLUMN     "price" INTEGER NOT NULL;
