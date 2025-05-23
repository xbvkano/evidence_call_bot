/*
  Warnings:

  - You are about to drop the `test` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropTable
DROP TABLE "test";

-- CreateTable
CREATE TABLE "FormData" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "number" TEXT NOT NULL,
    "address" TEXT NOT NULL,
    "size" TEXT NOT NULL,
    "date" TIMESTAMP(3) NOT NULL,
    "service" TEXT NOT NULL,
    "baseboards" BOOLEAN NOT NULL DEFAULT false,
    "fridgeInside" BOOLEAN NOT NULL DEFAULT false,
    "ovenInside" BOOLEAN NOT NULL DEFAULT false,
    "blinds" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "FormData_pkey" PRIMARY KEY ("id")
);
